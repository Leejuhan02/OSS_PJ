"""AT-1 표본의 PyPI 응답 사본(at1_pypi_info.json)을 다시 만드는 스크립트 (R0).

실제 PyPI 를 조회하므로 테스트가 아니라 사람이 필요할 때만 실행함. 테스트는 만들어진 사본만 읽음 (DC-05).

    python tests/fixtures/make_at1_snapshot.py

- 입력: at1_webapp_requirements.txt (AT-1 1·2단계)와, 그 끝에 jsonschema[format] 을 더한 입력 (AT-1 3단계)
- 저장: 전개 중 만난 모든 패키지의 info 중 식별·전개에 쓰는 필드만 이름순으로 저장함
- 사본을 다시 만들면 PyPI 의 새 버전 때문에 패키지 수가 바뀔 수 있음. 그때는 test_AT_1_webapp_sample.py 가 실패해 알려 줌
"""

import json
from operator import itemgetter
from pathlib import Path

from oss_check.adapters.pypi_adapter import PyPIPackageSource
from oss_check.collect.parser import parse_requirements
from oss_check.collect.walker import walk_with_warnings
from oss_check.domain.ports import PackageSource

HERE = Path(__file__).resolve().parent
INPUT = HERE / "at1_webapp_requirements.txt"
OUTPUT = HERE / "at1_pypi_info.json"
STEP3_EXTRA = "jsonschema[format]"                    # AT-1 3단계에서 추가로 입력하는 줄
KEPT_FIELDS = ("name", "version", "license_expression", "license", "classifiers", "requires_dist")


# [강의] 인터페이스 어댑터 — 포트를 감싸는 기록용 어댑터
#   - PackageSource 를 그대로 구현해 walker 에 넘기고, 받은 응답을 옆에 기록함
#   - walker 가 실제로 조회한 패키지만 사본에 남기려는 것임. 목록을 따로 손으로 만들지 않음
class RecordingSource(PackageSource):
    def __init__(self, inner: PackageSource):
        self._inner = inner
        self.seen: dict[str, dict] = {}

    def fetch(self, name: str) -> dict | None:
        info = self._inner.fetch(name)
        if info is not None:
            self.seen[name] = {key: info.get(key) for key in KEPT_FIELDS}
        return info


def main() -> None:
    base = INPUT.read_text(encoding="utf-8")
    source = RecordingSource(PyPIPackageSource())
    for text in (base, base + STEP3_EXTRA + "\n"):
        requirements, _ = parse_requirements(text)
        walk_with_warnings(requirements, source)
    # [강의] operator.itemgetter
    #   - (이름, info) 쌍을 이름으로 정렬하는 키로 씀
    #   - 사본을 다시 만들어도 줄 순서가 같게 유지되어, git 차이에 실제 바뀐 내용만 보이게 하려는 것임
    ordered = dict(sorted(source.seen.items(), key=itemgetter(0)))
    OUTPUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(ordered)}개 패키지 응답을 {OUTPUT.name} 에 저장함")


if __name__ == "__main__":
    main()

"""app·CLI 테스트용 가짜 객체 (R0). 테스트 파일이 아님 — 이름이 test_로 시작하지 않아 pytest가 수집하지 않음.

# [강의] 테스트 패턴 — 가짜 객체
#   - PackageSource·identify·judge를 같은 규격의 가짜로 바꿔 끼움
#   - 네트워크 없이(DC-05), 그리고 R2·R3 구현과 무관하게 조정 순서만 확인하려는 것임
"""

from collections import Counter

from oss_check.domain.models import Judgement, LicenseInfo
from oss_check.domain.ports import PackageSource

# 식별자 → 판정. 판정 5종이 하나씩 나오게 고름
VERDICT_BY_ID = {
    "GPL-3.0-only": "안 됨",
    "LGPL-2.1-only": "조건 있음",
    "Unlisted-1.0": "판단보류",
    "MIT": "써도 됨",
}


class CountingSource(PackageSource):
    """PyPI info 사본을 돌려주고, 이름별 호출 횟수를 셈. 없는 이름은 None (조회 실패)."""

    def __init__(self, infos: dict[str, dict]):
        self._infos = infos
        self.calls: Counter[str] = Counter()

    def fetch(self, name: str) -> dict | None:
        self.calls[name] += 1
        return self._infos.get(name)


class RecordingIdentify:
    """resolve.identify(name, info) 대역. license_expression 하나만 읽음."""

    def __init__(self):
        self.called: list[str] = []

    def __call__(self, name: str, info: dict) -> LicenseInfo:
        self.called.append(name)
        expr = info.get("license_expression")
        if not expr:
            return LicenseInfo.unknown(name)
        return LicenseInfo.single(name, expr, confidence="확실", origin="license_expression", raw=expr)


class RecordingJudge:
    """judge(lic, *, project) 대역. 받은 project를 기록함."""

    def __init__(self):
        self.projects: list[str] = []

    def __call__(self, lic: LicenseInfo, *, project: str) -> Judgement:
        self.projects.append(project)
        if lic.options is None:
            return Judgement(lic.package, "모름", "표기가 없음")
        (identifier,) = lic.identifiers
        return Judgement(lic.package, VERDICT_BY_ID[identifier], f"{identifier} 판정", identifier)


def info(expr: str | None = None, *deps: str) -> dict:
    """PyPI info dict 사본을 간단히 만듦."""
    return {"license_expression": expr, "requires_dist": list(deps) or None}


# 판정 5종이 모두 나오는 입력. ghost 는 PyPI에 없음(조회 실패)
TEXT = "\n".join(["mit-pkg==1.0", "gpl-pkg", "-e .", "ghost"])
INFOS = {
    "mit-pkg": info("MIT", "lgpl-dep", "unlisted-dep"),
    "gpl-pkg": info("GPL-3.0-only", "lgpl-dep"),
    "lgpl-dep": info("LGPL-2.1-only"),
    "unlisted-dep": info("Unlisted-1.0"),
}

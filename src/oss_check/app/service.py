"""분석 조정자 (R0). 설계지침 §4.0 흐름을 순서대로 부르고 Report를 만듦.

    parse_requirements(R1) → walk_with_warnings(R1) → identify(R2) → judge(R3) → Report

요구사항
- FR-DEP-05: 전개(R1)와 식별(R2)이 같은 info를 쓰도록, 패키지마다 한 번만 조회함
- FR-DEP-08: 조회 실패 패키지는 식별을 건너뛰고 「모름」, 사유 「패키지 정보를 가져오지 못함」
- FR-OUT-02: 행을 위험 순으로 담음
- FR-OUT-05: parser·walker 경고를 Report.warnings에 모음
- FR-IN-08: 1MB 초과 입력은 parser가 ValueError를 냄. 이 함수는 그대로 올려 보내고 web·CLI가 원인 설명으로 바꿈 (QR-R-01)
"""

from collections.abc import Callable
from functools import partial
from operator import attrgetter

from oss_check.collect.parser import parse_requirements
from oss_check.collect.walker import walk_with_warnings
from oss_check.domain.models import RISK_ORDER, Judgement, LicenseInfo, Package, Report, Row
from oss_check.domain.ports import PackageSource

# [강의] 애플리케이션 계층 (클린 아키텍처)
#   - analyze() 는 collect → resolve → judge 를 순서대로 부르기만 함. 식별·판정 로직은 여기 없음
#   - web(R5)과 CLI(R0)가 같은 함수를 불러 같은 결과를 냄 (IF-UI-04). 화면이 바뀌어도 이 파일은 그대로임

FETCH_FAILED_REASON = "패키지 정보를 가져오지 못함"   # FR-DEP-08, 설계지침 §4.3 app

# [강의] 함수 어노테이션 — 주입받는 함수의 모양을 이름으로 고정함
Identify = Callable[[str, dict], LicenseInfo]   # resolve.identify(name, info)   — R2
Judge = Callable[..., Judgement]                # judge(lic, *, project)          — R3


class ComponentMissing(RuntimeError):
    """§4.0의 함수가 아직 저장소에 없음. 어떤 이름이 없는지 메시지에 적음."""


class _FetchOnce(PackageSource):
    """같은 이름은 한 번만 조회하고 결과(실패 None 포함)를 재사용함 — FR-DEP-05.

    포트를 그대로 구현해 감싸므로 walker(R1)는 차이를 모름. walker와 identify(R2)가 같은 info를 쓰게 하는 용도임.
    유효 기간이 있는 캐시(FR-VUL·IF-SW)는 adapters(R4)의 몫이라, 여기서는 분석 1회 범위만 기억함.
    """

    def __init__(self, inner: PackageSource):
        self._inner = inner
        self._seen: dict[str, dict | None] = {}

    def fetch(self, name: str) -> dict | None:
        if name not in self._seen:
            self._seen[name] = self._inner.fetch(name)
        return self._seen[name]


def _default_identify() -> Identify:
    try:
        from oss_check.resolve import identify
    except ImportError as error:
        raise ComponentMissing("resolve.identify(name, info) 가 아직 없음 (설계지침 §4.0, R2 담당)") from error
    return identify


def _default_judge() -> Judge:
    from oss_check.judge.judge_logic import judge
    return judge


def _failed_row(package: Package) -> Row:
    """FR-DEP-08: 조회 실패 패키지는 식별·판정 규칙을 거치지 않고 「모름」과 고정 사유로 채움."""
    return Row(package, LicenseInfo.unknown(package.name),
               Judgement(package.name, "모름", FETCH_FAILED_REASON))


# [강의] 키워드 전용 인수 — project·source 는 반드시 이름으로 넘김. 순서를 바꿔 넘기는 실수를 막음
def analyze(text: str | bytes, *, project: str, source: PackageSource,
            identify: Identify | None = None, judge: Judge | None = None) -> Report:
    """requirements 텍스트를 분석해 위험 순으로 정렬된 Report를 돌려줌.

    project   프로젝트 라이선스 SPDX ID. 기본값 MIT는 호출하는 쪽이 parser.get_project_license()로 정함 (FR-IN-06)
    source    PackageSource 구현. 실제는 adapters(R4), 테스트는 가짜 (DC-05)
    identify  생략하면 resolve.identify (R2). 없으면 ComponentMissing
    judge     생략하면 judge.judge_logic.judge (R3)
    """
    identify = identify or _default_identify()
    judge = judge or _default_judge()
    source = _FetchOnce(source)

    requirements, parse_warnings = parse_requirements(text)
    packages, walk_warnings = walk_with_warnings(requirements, source)
    infos = [source.fetch(p.name) for p in packages]           # 이미 조회한 값 재사용 — FR-DEP-05

    # FR-DEP-08: 조회 실패 패키지를 먼저 떼어 냄. walker 가 lookup_failed 를 표시하지 않은 경우도 info None 으로 잡음
    found = [(p, i) for p, i in zip(packages, infos) if not (p.lookup_failed or i is None)]
    failed = [p for p, i in zip(packages, infos) if p.lookup_failed or i is None]

    licenses = [identify(p.name, i) for p, i in found]

    # [강의] functools.partial
    #   - judge(lic, *, project) 의 project 를 고정해 인수 하나짜리 함수로 만듦
    #   - 패키지마다 project= 를 반복해 넘기지 않고, 아래 map 에 바로 넘기려는 것임
    judge_one = partial(judge, project=project)
    # [강의] 고차 함수 (map)
    #   - 판정 함수를 값으로 넘겨 패키지마다 적용함
    #   - 조정자는 「무엇을 부를지」만 정하고 판정 방법은 R3 함수에 맡김
    judgements = list(map(judge_one, licenses))

    rows = [Row(p, lic, j) for (p, _), lic, j in zip(found, licenses, judgements)]
    rows += [_failed_row(p) for p in failed]

    # [강의] operator.attrgetter
    #   - 중첩 속성 package.name 을 정렬 키로 씀
    #   - lambda r: r.package.name 과 같지만 이름으로 의도가 드러남
    rows.sort(key=attrgetter("package.name"))
    # [강의] lambda
    #   - 판정 → 위험 순위로 바꾸는 한 줄짜리 키 함수
    #   - sort 는 안정 정렬이라 같은 판정 안에서는 앞 단계의 이름순이 유지됨 (FR-OUT-02)
    rows.sort(key=lambda row: RISK_ORDER[row.judgement.verdict])

    return Report(project, rows, parse_warnings + walk_warnings)

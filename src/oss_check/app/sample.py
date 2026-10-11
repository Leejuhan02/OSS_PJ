"""R5 화면 개발용 가짜 결과 (R0). 실제 분석(PyPI 조회) 없이 Report 하나를 만듦.

- 패키지 5개, 판정 5종이 하나씩 있음. 직접 3 · 따라온 2 · 조회 실패 1
- rows 는 일부러 위험 순이 아님. 화면은 Report.sorted_rows() 로 정렬해야 함 (설계지침 §4.3 web)
- 패키지 이름은 모두 지어낸 것임 (sample-*)

사용 예 (web 테스트·화면 확인)
    from oss_check.app.sample import sample_report
    report = sample_report()
    templates.TemplateResponse(request=request, name="result.html", context={"report": report})
"""

from oss_check.app.service import FETCH_FAILED_REASON
from oss_check.domain.models import Judgement, LicenseInfo, Package, Report, Row


def _row(package: Package, lic: LicenseInfo, verdict: str, reason: str, decisive: str | None = None) -> Row:
    return Row(package, lic, Judgement(package.name, verdict, reason, decisive))


def sample_report() -> Report:
    """호출할 때마다 새 Report를 만듦 (Report는 바꿀 수 있는 객체라 공유하지 않음)."""
    rows = [
        _row(Package("sample-gpl", "2.0"),
             LicenseInfo.single("sample-gpl", "GPL-3.0-only", confidence="확실",
                                origin="license_expression", raw="GPL-3.0-only"),
             "안 됨", "GPL-3.0-only 조건이 내 프로젝트보다 셈", "GPL-3.0-only"),
        _row(Package("sample-lgpl", "1.4", direct=False, depth=1),
             LicenseInfo.single("sample-lgpl", "LGPL-2.1-or-later", confidence="추정",
                                origin="classifiers",
                                raw="License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)"),
             "조건 있음", "LGPL-2.1-or-later: 고쳐 썼다면 고친 부분만 공개", "LGPL-2.1-or-later"),
        _row(Package("sample-missing", lookup_failed=True),
             LicenseInfo.unknown("sample-missing"),
             "모름", FETCH_FAILED_REASON),
        _row(Package("sample-mit", "3.1"),
             LicenseInfo("sample-mit", (frozenset({"MIT"}), frozenset({"Apache-2.0"})),
                         "확실", "license_expression", "MIT OR Apache-2.0"),
             "써도 됨", "MIT: 사용 가능", "MIT"),
        _row(Package("sample-unlisted", direct=False, depth=2),
             LicenseInfo.single("sample-unlisted", "EUPL-1.2", confidence="확실",
                                origin="license_expression", raw="EUPL-1.2"),
             "판단보류", "등급표에 없는 라이선스임"),
    ]
    warnings = [
        "Line 3: '-e .' - 지원하지 않는 옵션('-e')입니다.",
        "패키지 'sample-missing'의 정보를 가져오지 못했습니다 (조회 실패).",
    ]
    return Report("MIT", rows, warnings)

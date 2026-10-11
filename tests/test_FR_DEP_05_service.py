"""FR-DEP-05: 의존성 전개와 라이선스 식별을 합쳐도 같은 패키지는 한 번만 조회함 (설계지침 §4.3 app)."""

from app_fakes import INFOS, TEXT, CountingSource, RecordingIdentify, RecordingJudge
from oss_check.app.service import analyze


def test_each_package_is_fetched_once():
    """FR-DEP-05: lgpl-dep 은 두 패키지가 끌어오지만 조회는 1번. ghost(실패)도 1번"""
    source = CountingSource(INFOS)
    analyze(TEXT, project="MIT", source=source, identify=RecordingIdentify(), judge=RecordingJudge())
    assert dict(source.calls) == {
        "mit-pkg": 1, "gpl-pkg": 1, "ghost": 1, "lgpl-dep": 1, "unlisted-dep": 1}

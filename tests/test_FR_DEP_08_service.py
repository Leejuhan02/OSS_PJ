"""FR-DEP-08: 조회 실패 패키지는 라이선스 식별을 건너뛰고 「모름」, 사유 「패키지 정보를 가져오지 못함」 (설계지침 §4.3 app)."""

import pytest

from app_fakes import INFOS, TEXT, CountingSource, RecordingIdentify, RecordingJudge
from oss_check.app.service import FETCH_FAILED_REASON, analyze


@pytest.fixture
def result():
    identify = RecordingIdentify()
    report = analyze(TEXT, project="MIT", source=CountingSource(INFOS),
                     identify=identify, judge=RecordingJudge())
    row = next(r for r in report.rows if r.package.name == "ghost")
    return report, row, identify


def test_failed_package_stays_in_report(result):
    """FR-DEP-08: 분석을 멈추지 않고 그 패키지를 결과에 남김"""
    report, row, _ = result
    assert len(report.rows) == 5


def test_failed_package_is_unknown_with_reason(result):
    """FR-DEP-08: 판정 「모름」, 사유 「패키지 정보를 가져오지 못함」, 라이선스 미상"""
    _, row, _ = result
    assert row.judgement.verdict == "모름"
    assert row.judgement.reason == FETCH_FAILED_REASON == "패키지 정보를 가져오지 못함"
    assert row.license.options is None


def test_identify_is_skipped_for_failed_package(result):
    """FR-DEP-08: 조회 실패 패키지는 식별 함수에 넘기지 않음"""
    _, _, identify = result
    assert "ghost" not in identify.called
    assert sorted(identify.called) == ["gpl-pkg", "lgpl-dep", "mit-pkg", "unlisted-dep"]

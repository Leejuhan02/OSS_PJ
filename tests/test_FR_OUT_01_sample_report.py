"""FR-OUT-01~05: R5 화면 개발용 가짜 결과 app.sample.sample_report(). 실제 분석 없이 Report 한 개를 돌려줌."""

from oss_check.app.sample import sample_report
from oss_check.app.service import FETCH_FAILED_REASON
from oss_check.domain.models import VERDICTS, Report


def test_sample_has_every_verdict_once():
    """FR-OUT-02: 판정 5종이 하나씩 있고, sorted_rows()가 위험 순으로 늘어놓음"""
    report = sample_report()
    assert isinstance(report, Report)
    assert [r.judgement.verdict for r in report.sorted_rows()] == list(VERDICTS)


def test_sample_rows_are_not_presorted():
    """FR-OUT-02: 저장 순서는 위험 순이 아님 — 화면이 sorted_rows()를 쓰는지 확인할 수 있게 함"""
    report = sample_report()
    assert report.rows != report.sorted_rows()


def test_sample_counts():
    """FR-OUT-01·FR-DEP-08: 전체 5, 직접 3, 따라온 2, 조회 실패 1"""
    assert sample_report().counts() == {"total": 5, "direct": 3, "transitive": 2, "failed": 1}


def test_sample_failed_row_and_warnings():
    """FR-DEP-08·FR-OUT-05: 조회 실패 줄의 사유, 경고 2건(건너뛴 줄, 조회 실패)"""
    report = sample_report()
    failed = [r for r in report.rows if r.package.lookup_failed]
    assert [r.judgement.reason for r in failed] == [FETCH_FAILED_REASON]
    assert len(report.warnings) == 2


def test_sample_is_new_each_call():
    """Report는 바꿀 수 있는 객체라 호출마다 새로 만듦. 한 테스트가 고쳐도 다른 테스트에 번지지 않음"""
    first = sample_report()
    first.rows.clear()
    assert len(sample_report().rows) == 5

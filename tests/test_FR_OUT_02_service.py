"""FR-OUT-02: app.service.analyze()가 판정 결과를 위험 순으로 담은 Report를 돌려줌 (설계지침 §4.0·§5.5)."""

from app_fakes import INFOS, TEXT, CountingSource, RecordingIdentify, RecordingJudge
from oss_check.app.service import analyze
from oss_check.domain.models import Report


def run(project="MIT"):
    judge = RecordingJudge()
    report = analyze(TEXT, project=project, source=CountingSource(INFOS),
                     identify=RecordingIdentify(), judge=judge)
    return report, judge


def test_returns_report_with_one_row_per_package():
    """FR-OUT-02: 직접 3개(ghost 포함) + 따라온 2개 = 5줄"""
    report, _ = run()
    assert isinstance(report, Report)
    assert sorted(r.package.name for r in report.rows) == [
        "ghost", "gpl-pkg", "lgpl-dep", "mit-pkg", "unlisted-dep"]


def test_rows_are_in_risk_order():
    """FR-OUT-02: 안 됨 → 모름 → 조건 있음 → 판단보류 → 써도 됨"""
    report, _ = run()
    assert [r.judgement.verdict for r in report.rows] == [
        "안 됨", "모름", "조건 있음", "판단보류", "써도 됨"]
    assert report.rows == report.sorted_rows()


def test_project_license_is_passed_to_judge_and_report():
    """FR-IN-06·FR-OUT-02: 프로젝트 라이선스가 판정 함수와 Report에 그대로 전달됨"""
    report, judge = run(project="GPL-3.0-only")
    assert report.project_license == "GPL-3.0-only"
    assert judge.projects and set(judge.projects) == {"GPL-3.0-only"}

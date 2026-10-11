"""FR-OUT-05: 분석 중 생긴 경고(건너뛴 줄, 조회 실패)를 Report.warnings에 함께 담음."""

import pytest

from app_fakes import INFOS, TEXT, CountingSource, RecordingIdentify, RecordingJudge
from oss_check.app import service
from oss_check.app.service import analyze


def test_parser_and_walker_warnings_are_kept():
    """FR-OUT-05: 3번째 줄 `-e .` 경고(R1 parser)와 ghost 조회 실패 경고(R1 walker)가 모두 있음"""
    report = analyze(TEXT, project="MIT", source=CountingSource(INFOS),
                     identify=RecordingIdentify(), judge=RecordingJudge())
    assert any("Line 3" in w for w in report.warnings)
    assert any("ghost" in w for w in report.warnings)


def test_oversized_input_raises_value_error():
    """FR-IN-08·QR-R-01: 1MB 초과 입력은 분석하지 않고 ValueError (web·CLI가 원인 설명으로 바꿔 보여줌)"""
    with pytest.raises(ValueError):
        analyze("a\n" * 600_000, project="MIT", source=CountingSource({}),
                identify=RecordingIdentify(), judge=RecordingJudge())


def test_missing_identify_gives_clear_error(monkeypatch):
    """§4.0: resolve.identify 가 아직 없으면 무엇이 없는지 알려 줌 (R2 작업 전 상태)"""
    import oss_check.resolve as resolve
    monkeypatch.delattr(resolve, "identify", raising=False)
    with pytest.raises(service.ComponentMissing, match="identify"):
        analyze("mit-pkg", project="MIT", source=CountingSource(INFOS), judge=RecordingJudge())

"""FR-OUT-05: 분석 중 생긴 경고(건너뛴 줄, 조회 실패)를 Report.warnings에 함께 담음."""

import pytest

from app_fakes import INFOS, TEXT, CountingSource, RecordingIdentify, RecordingJudge
from oss_check.app import service
from oss_check.app.service import analyze
from oss_check.collect.parser import parse_requirements


def test_parser_and_walker_warnings_are_kept():
    """FR-OUT-05: parser 경고(3번째 줄 `-e .`)와 walker 경고(ghost 조회 실패)가 모두 있음

    경고 문구는 R1이 정함. 여기서는 문구를 다시 적지 않고 parser가 낸 경고가 그대로 전달되는지만 봄
    """
    report = analyze(TEXT, project="MIT", source=CountingSource(INFOS),
                     identify=RecordingIdentify(), judge=RecordingJudge())
    parser_warnings = parse_requirements(TEXT)[1]
    assert parser_warnings and all(w in report.warnings for w in parser_warnings)
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

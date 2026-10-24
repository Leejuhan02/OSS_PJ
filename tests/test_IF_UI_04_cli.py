"""IF-UI-04: 명령줄에서 `python -m oss_check <파일>`로 웹과 같은 분석을 실행함."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app_fakes import INFOS, TEXT, CountingSource, RecordingIdentify, RecordingJudge
from oss_check.__main__ import format_report, main
from oss_check.app.sample import sample_report
from oss_check.collect.parser import parse_requirements

SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.fixture
def req_file(tmp_path):
    path = tmp_path / "requirements.txt"
    path.write_text(TEXT, encoding="utf-8")
    return path


def run(argv, judge=None):
    return main(argv, source=CountingSource(INFOS), identify=RecordingIdentify(),
                judge=judge or RecordingJudge())


def test_prints_rows_in_risk_order(req_file, capsys):
    """IF-UI-04·FR-OUT-02: 종료 코드 0, 판정이 위험 순으로 출력됨"""
    assert run([str(req_file)]) == 0
    out = capsys.readouterr().out
    positions = [out.index(f"[{v}]") for v in ("안 됨", "모름", "조건 있음", "판단보류", "써도 됨")]
    assert positions == sorted(positions)


def test_prints_counts_and_warnings(req_file, capsys):
    """FR-OUT-01·FR-OUT-05: 개수 줄과 경고가 함께 출력됨"""
    run([str(req_file)])
    out = capsys.readouterr().out
    assert "패키지 5개 (직접 3 · 따라온 2" in out
    # 경고 문구는 R1이 정함. parser가 낸 경고가 그대로 출력되는지만 봄
    assert all(w in out for w in parse_requirements(TEXT)[1])


def test_project_defaults_to_mit(req_file):
    """FR-IN-06: --project 를 주지 않으면 MIT"""
    judge = RecordingJudge()
    run([str(req_file)], judge=judge)
    assert set(judge.projects) == {"MIT"}


def test_project_option(req_file):
    """FR-IN-06: --project 로 프로젝트 라이선스를 바꿈"""
    judge = RecordingJudge()
    run([str(req_file), "--project", "Apache-2.0"], judge=judge)
    assert set(judge.projects) == {"Apache-2.0"}


def test_missing_file_is_explained(tmp_path, capsys):
    """QR-R-01: 없는 파일이면 추적 정보 대신 원인을 알리고 종료 코드 1"""
    missing = tmp_path / "nope.txt"
    assert run([str(missing)]) == 1
    assert "nope.txt" in capsys.readouterr().err


def test_oversized_file_is_explained(tmp_path, capsys):
    """FR-IN-08·QR-R-01: 1MB 초과면 분석하지 않고 원인을 알림"""
    big = tmp_path / "big.txt"
    big.write_text("a\n" * 600_000, encoding="utf-8")
    assert run([str(big)]) == 1
    assert "1MB" in capsys.readouterr().err


def test_missing_pypi_source_is_explained(req_file, capsys, monkeypatch):
    """§4.0: R4의 PyPIPackageSource 가 아직 없으면 무엇이 없는지 알리고 종료 코드 1"""
    import oss_check.adapters.pypi_adapter as adapter
    monkeypatch.delattr(adapter, "PyPIPackageSource", raising=False)
    assert main([str(req_file)], identify=RecordingIdentify(), judge=RecordingJudge()) == 1
    assert "PyPIPackageSource" in capsys.readouterr().err


def test_module_entry_point():
    """IF-UI-04: `python -m oss_check --help` 가 실행됨"""
    env = dict(os.environ, PYTHONPATH=str(SRC), PYTHONIOENCODING="utf-8")
    done = subprocess.run([sys.executable, "-m", "oss_check", "--help"],
                          capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
    assert done.returncode == 0, done.stderr
    assert "--project" in done.stdout


def test_output_is_cp949_safe():
    """IF-UI-04: 윈도우에서 결과를 파일로 저장(cp949)해도 인코딩 오류가 나지 않음"""
    format_report(sample_report()).encode("cp949")

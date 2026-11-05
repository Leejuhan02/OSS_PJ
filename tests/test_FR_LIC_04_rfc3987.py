"""FR-LIC-04: 실제 rfc3987 표기로 AT-1 3단계의 식별·판정 연결을 확인한다."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from oss_check.__main__ import main
from oss_check.app.service import analyze
from oss_check.domain.ports import PackageSource
from oss_check.resolve import identify
from oss_check.web.main import app
from oss_check.web.routers import pages


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class SnapshotSource(PackageSource):
    """FR-LIC-04: 동봉 응답만 쓰고 누락·중복 조회를 숨기지 않는 가짜 소스."""

    def __init__(self, infos):
        self.infos = infos
        self.calls = []

    def fetch(self, name):
        self.calls.append(name)
        assert name in self.infos, f"사본에 없는 패키지: {name}"
        return self.infos[name]


@pytest.fixture(scope="module")
def infos():
    return json.loads((FIXTURES / "at1_pypi_info.json").read_text(encoding="utf-8"))


def test_rfc3987_uses_versioned_legacy_license(infos):
    """FR-LIC-04: GNU GPLv3+를 버전·이후 버전 허용을 보존해 식별한다."""
    info = infos["rfc3987"]
    assert info["license"] == "GNU GPLv3+"
    result = identify("rfc3987", info)
    assert result.options == (frozenset({"GPL-3.0-or-later"}),)
    assert (result.origin, result.confidence, result.raw) == ("license", "확실", info["license"])


@pytest.mark.parametrize("with_base", [False, True])
def test_at1_step3_blocks_rfc3987_and_preserves_counts(infos, with_base):
    """FR-LIC-04 / AT-1: 단독·웹앱 표본 추가 입력 모두 GPL 근거로 안 됨."""
    base = (FIXTURES / "at1_webapp_requirements.txt").read_text(encoding="utf-8")
    text = (base if with_base else "") + "jsonschema[format]\n"
    source = SnapshotSource(infos)
    report = analyze(text, project="MIT", source=source)
    row = next(row for row in report.rows if row.package.name == "rfc3987")
    assert row.license.options == (frozenset({"GPL-3.0-or-later"}),)
    assert row.judgement.verdict == "안 됨"
    assert row.judgement.decisive_license == "GPL-3.0-or-later"
    assert report.rows[0].package.name == "rfc3987"
    assert report.counts()["failed"] == 0
    assert report.counts()["direct"] == (12 if with_base else 1)
    assert len(source.calls) == len(set(source.calls))
    if not with_base:
        assert report.counts() == {"total": 18, "direct": 1, "transitive": 17, "failed": 0}


def test_at1_step3_is_consistent_in_web_and_cli(monkeypatch, tmp_path, capsys, infos):
    """FR-LIC-04 / AT-1: 실제 웹 경로·CLI에 같은 안 됨 판정과 식별자가 표시됨."""
    text = (FIXTURES / "at1_webapp_requirements.txt").read_text(encoding="utf-8")
    text += "jsonschema[format]\n"
    monkeypatch.setattr(pages, "PyPIPackageSource", lambda: SnapshotSource(infos))
    with TestClient(app) as client:
        response = client.post("/analyze", data={"dependency_text": text, "project_license": "MIT"})
    assert response.status_code == 200
    assert "<h3>안 됨 · rfc3987</h3>" in response.text
    assert "GPL-3.0-or-later" in response.text
    assert response.text.index("안 됨 · rfc3987") < response.text.index("조건 있음 · certifi")
    path = tmp_path / "requirements.txt"
    path.write_text(text, encoding="utf-8")
    assert main([str(path)], source=SnapshotSource(infos)) == 0
    assert "[안 됨] rfc3987" in capsys.readouterr().out

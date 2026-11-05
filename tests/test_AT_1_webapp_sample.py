"""AT-1: 최소 완성본 인수 시나리오를 「웹앱 구성 11줄」 표본으로 네트워크 없이 확인함 (SRS §4.3).

입력 tests/fixtures/at1_webapp_requirements.txt 는 타당성 검증(2026-09-30)의 「웹앱 (이 프로젝트 예상 구성)」 표본임.
PyPI 응답은 tests/fixtures/at1_pypi_info.json 사본을 씀 (DC-05, 설계지침 §9.2). 사본 갱신은 make_at1_snapshot.py.

이 파일이 확인하는 단계
- 2단계: 「30개 (직접 11 · 따라온 19)」, certifi 「조건 있음」
- 4단계: 결과 화면 하단의 법적 고지, 데이터 출처
- 5단계: 같은 입력을 CLI로 실행하면 웹과 같은 판정
확인하지 않는 단계
- 1단계 「30초 안에 결과」: 실제 네트워크 시간이라 측정(QR-P-01)으로 따로 확인함
- 3단계 jsonschema[format] → rfc3987 「안 됨」: R2 별칭(GNU GPLv3+) 반영 후 R2가 추가함. 사본에는 3단계 패키지도 들어 있음
- 6단계 Docker: 실행 환경 점검(R5)으로 확인함
"""

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from oss_check.__main__ import main
from oss_check.app.service import analyze
from oss_check.collect.parser import parse_requirements
from oss_check.domain.ports import PackageSource
from oss_check.web.main import app
from oss_check.web.routers import pages

FIXTURES = Path(__file__).resolve().parent / "fixtures"
INPUT = FIXTURES / "at1_webapp_requirements.txt"
SNAPSHOT = FIXTURES / "at1_pypi_info.json"
VERDICT_LINE = re.compile(r"^\[(안 됨|모름|조건 있음|판단보류|써도 됨)\] ([a-z0-9][a-z0-9-]*)", re.M)
VERDICT_HTML = re.compile(r"<h3>(안 됨|모름|조건 있음|판단보류|써도 됨) · ([a-z0-9][a-z0-9-]*)</h3>")


# [강의] ABC — 포트 구현 / 테스트 패턴 — 가짜 객체
#   - domain.ports.PackageSource 를 상속해 PyPI 대신 저장해 둔 응답 사본을 돌려줌
#   - 사본에 없는 이름을 물으면 None(조회 실패)이 아니라 오류를 냄. 사본이 빠진 것을 「조회 실패」로 숨기지 않으려는 것임
class SnapshotSource(PackageSource):
    def __init__(self, infos: dict[str, dict]):
        self._infos = infos

    def fetch(self, name: str) -> dict | None:
        if name not in self._infos:
            raise AssertionError(f"응답 사본에 없는 패키지: {name} — make_at1_snapshot.py 로 사본을 다시 만들 것")
        return self._infos[name]


@pytest.fixture(scope="module")
def text() -> str:
    return INPUT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def infos() -> dict[str, dict]:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report(text, infos):
    return analyze(text, project="MIT", source=SnapshotSource(infos))


def test_input_is_11_direct_lines(text):
    """AT-1 1단계: 입력 파일은 11줄이고, 11줄 모두 경고 없이 해석됨 (FR-IN-03·04)"""
    requirements, warnings = parse_requirements(text)
    assert len(text.splitlines()) == 11
    assert len(requirements) == 11
    assert warnings == []


def test_counts_match_scenario(report):
    """AT-1 2단계: 「30개 (직접 11 · 따라온 19)」, 조회 실패 0 (FR-OUT-01, FR-DEP-01)"""
    assert report.counts() == {"total": 30, "direct": 11, "transitive": 19, "failed": 0}


def test_certifi_is_conditional(report):
    """AT-1 2단계: 따라온 패키지 certifi 가 「조건 있음」 (FR-JDG-05)"""
    row = next(r for r in report.rows if r.package.name == "certifi")
    assert not row.package.direct
    assert row.judgement.verdict == "조건 있음"


def test_result_page_footer(monkeypatch, text, infos):
    """AT-1 4단계: 실제 결과 화면에 법적 고지와 데이터 출처가 있음 (CR-01, CR-04)"""
    monkeypatch.setattr(pages, "PyPIPackageSource", lambda: SnapshotSource(infos))
    with TestClient(app) as client:
        html = client.post("/analyze", data={"dependency_text": text, "project_license": "MIT"}).text
    assert "법적 조언이 아닙니다" in html
    assert all(source in html for source in ("SPDX", "PyPI", "OSV"))


def test_cli_and_web_give_same_verdicts(monkeypatch, tmp_path, capsys, text, infos):
    """AT-1 5단계: 같은 입력을 CLI 와 웹으로 실행하면 패키지별 판정이 같음 (IF-UI-04)"""
    req = tmp_path / "requirements.txt"
    req.write_text(text, encoding="utf-8")
    assert main([str(req)], source=SnapshotSource(infos)) == 0
    cli = {name: verdict for verdict, name in VERDICT_LINE.findall(capsys.readouterr().out)}

    monkeypatch.setattr(pages, "PyPIPackageSource", lambda: SnapshotSource(infos))
    with TestClient(app) as client:
        html = client.post("/analyze", data={"dependency_text": text, "project_license": "MIT"}).text
    web = {name: verdict for verdict, name in VERDICT_HTML.findall(html)}

    assert len(cli) == 30
    assert cli == web

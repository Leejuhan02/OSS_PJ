"""QR-S-04: 사용자 입력과 외부 결과를 HTML 문자로 안전하게 표시함."""

from dataclasses import replace

from fastapi.testclient import TestClient
from web_fakes import install_web_source

from oss_check.app.sample import sample_report
from oss_check.web.main import app
from oss_check.web.routers import pages


def test_restored_input_cannot_escape_textarea():
    """QR-S-04: 복원한 텍스트가 textarea를 닫거나 스크립트를 만들지 않음."""
    payload = '</textarea><script>alert("test")</script>'
    with TestClient(app) as client:
        response = client.post("/analyze", data={
            "dependency_text": payload, "project_license": "Apache-2.0",
        }, files={"dependency_file": ("requirements.txt", b"requests", "text/plain")})
    assert response.status_code == 400
    assert payload not in response.text
    assert "&lt;/textarea&gt;&lt;script&gt;" in response.text
    assert "<script>" not in response.text


def test_received_license_is_escaped(monkeypatch):
    """QR-S-04: 직접 전송한 라이선스 값도 HTML로 실행되지 않음."""
    install_web_source(monkeypatch)
    with TestClient(app) as client:
        response = client.post("/analyze", data={
            "dependency_text": "requests", "project_license": "<script>test</script>",
        })
    assert response.status_code == 200
    assert "&lt;script&gt;test&lt;/script&gt;" in response.text
    assert "<script>" not in response.text


def test_report_warnings_and_reasons_are_escaped(monkeypatch):
    """QR-S-04: 외부 데이터가 포함될 수 있는 경고와 사유도 이스케이프함."""
    report = sample_report()
    report.warnings = ["<script>warning</script>"]
    row = report.rows[0]
    report.rows[0] = replace(row, judgement=replace(
        row.judgement, reason="<script>reason</script>"))
    monkeypatch.setattr(pages, "sample_report", lambda: report)
    with TestClient(app) as client:
        response = client.get("/preview")
    assert response.status_code == 200
    assert "&lt;script&gt;warning&lt;/script&gt;" in response.text
    assert "&lt;script&gt;reason&lt;/script&gt;" in response.text
    assert "<script>" not in response.text

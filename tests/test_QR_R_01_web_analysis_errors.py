"""QR-R-01: 분석 실패를 내부 예외 대신 한국어 오류 화면으로 안내함."""

import pytest
from fastapi.testclient import TestClient
from web_fakes import install_web_source

from oss_check.app.service import ComponentMissing
from oss_check.web.main import app
from oss_check.web.routers import pages


@pytest.mark.parametrize(
    "error,status,message",
    [
        (ValueError("입력 처리 실패"), 400, "입력을 분석할 수 없습니다"),
        (ComponentMissing("아직 연결되지 않은 모듈"), 503, "분석 기능이 아직 준비되지 않았습니다"),
        (UnicodeEncodeError("latin-1", "한글", 0, 1, "private-detail"),
         503, "패키지 조회 설정 오류로 분석할 수 없습니다"),
    ],
    ids=["invalid-input", "component-missing", "header-encoding"],
)
def test_analysis_error_is_explained(monkeypatch, error, status, message):
    """QR-R-01: 원인을 안내하고 텍스트·라이선스를 복원하며 내부 오류를 숨김."""
    install_web_source(monkeypatch)

    def fail_analysis(*args, **kwargs):
        raise error

    monkeypatch.setattr(pages, "analyze", fail_analysis)
    with TestClient(app) as client:
        response = client.post("/analyze", data={
            "dependency_text": "requests==2.32.0", "project_license": "Apache-2.0",
        })
    assert response.status_code == status
    assert message in response.text
    assert ">requests==2.32.0</textarea>" in response.text
    assert 'value="Apache-2.0" selected' in response.text
    assert "Traceback" not in response.text
    assert "UnicodeEncodeError" not in response.text
    assert "private-detail" not in response.text
    assert "sample-gpl" not in response.text

"""IF-UI-01: 웹 폼 입력을 접수하고 분석 연결 전임을 안내함."""

import pytest
from fastapi.testclient import TestClient

from oss_check.web.main import app


@pytest.mark.parametrize(
    "data,files,expected",
    [
        ({"dependency_text": "requests", "project_license": "Apache-2.0"},
         None, "Apache-2.0"),
        ({"dependency_text": "requests"}, None, "MIT"),
        ({"project_license": "MIT"},
         {"dependency_file": ("requirements.txt", b"requests\n", "text/plain")}, "MIT"),
    ],
)
def test_form_accepts_input(data, files, expected):
    """IF-UI-01: 파일 또는 텍스트와 프로젝트 라이선스를 받음."""
    with TestClient(app) as client:
        response = client.post("/analyze", data=data, files=files)
    assert response.status_code == 200
    assert "입력을 받았습니다" in response.text
    assert "실제 분석은 아직 연결되지 않았습니다" in response.text
    assert f"프로젝트 라이선스: {expected}" in response.text


@pytest.mark.parametrize(
    "data,files,message",
    [
        ({}, None, "파일을 선택하거나 의존성 목록을 입력해 주세요"),
        ({"dependency_text": "requests"},
         {"dependency_file": ("requirements.txt", b"fastapi", "text/plain")},
         "파일과 직접 입력 중 하나만 사용해 주세요"),
        ({}, {"dependency_file": ("requirements.txt", b"\xff", "text/plain")},
         "UTF-8 텍스트 파일"),
    ],
)
def test_form_explains_invalid_input(data, files, message):
    """IF-UI-01: 접수할 수 없는 입력은 화면에서 원인을 안내함."""
    with TestClient(app) as client:
        response = client.post("/analyze", data=data, files=files)
    assert response.status_code == 400
    assert message in response.text

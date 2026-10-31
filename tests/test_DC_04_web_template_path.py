"""DC-04: 배포 실행을 위한 템플릿 경로의 보조 회귀 검사.

실행 폴더가 달라도 웹 화면을 찾는지만 검사함.
Docker 이미지 빌드·실행과 최종 인수 시나리오 통과를 대신하지 않음.
"""

import pytest
from fastapi.testclient import TestClient
from web_fakes import install_web_source

from oss_check.web.main import app


@pytest.mark.parametrize(
    "method,path,data,expected",
    [
        ("GET", "/", None, "의존성 라이선스·취약점 점검"),
        ("GET", "/preview", None, "실제 입력을 분석한 결과가 아닙니다"),
        ("POST", "/analyze", {"dependency_text": "requests"}, "의존성 점검 결과"),
    ],
    ids=["home", "preview", "input-received"],
)
def test_template_renders_outside_repository(monkeypatch, tmp_path, method, path, data, expected):
    """DC-04: 실행 위치에 의존하지 않는 입력·예시·접수 화면을 확인함."""
    install_web_source(monkeypatch)
    monkeypatch.chdir(tmp_path)
    with TestClient(app) as client:
        response = client.request(method, path, data=data)
    assert response.status_code == 200
    assert expected in response.text

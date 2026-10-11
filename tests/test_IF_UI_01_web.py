from fastapi.testclient import TestClient

from oss_check.web.main import app


client = TestClient(app)


def test_main_page():
    response = client.get("/")

    assert response.status_code == 200
    assert "의존성 라이선스·취약점 점검" in response.text
    assert "분석하기" in response.text
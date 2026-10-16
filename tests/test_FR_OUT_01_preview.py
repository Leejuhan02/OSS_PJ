"""FR-OUT-01: 예시 결과에서 전체·직접·따라온 패키지 수를 표시함."""

from fastapi.testclient import TestClient

from oss_check.web.main import app


def test_sample_preview_displays_report():
    """FR-OUT-01: 팀장 제공 예시 결과를 실제 분석과 구분해 표시함."""
    with TestClient(app) as client:
        response = client.get("/preview")
    assert response.status_code == 200
    assert "실제 입력을 분석한 결과가 아닙니다" in response.text
    assert "전체 5개" in response.text
    assert "직접 3개" in response.text
    assert "따라온 2개" in response.text
    assert "sample-gpl" in response.text
    assert "법적 조언이 아닙니다" in response.text
    assert "SPDX · PyPI · OSV" in response.text


def test_home_links_to_sample_preview():
    """FR-OUT-01: 입력을 제출하지 않고 예시 화면을 열 수 있음."""
    with TestClient(app) as client:
        response = client.get("/")
    assert 'href="/preview"' in response.text
    assert "예시 결과 보기" in response.text

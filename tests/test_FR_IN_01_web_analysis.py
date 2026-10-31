"""FR-IN-01: 업로드한 파일을 R0 분석에 전달하고 공통 Report를 표시함."""

import pytest
from fastapi.testclient import TestClient
from web_fakes import install_web_source

from oss_check.web.main import app


@pytest.mark.parametrize("project", ["MIT", "GPL-3.0-only"])
def test_uploaded_file_runs_analysis(monkeypatch, project):
    """FR-IN-01: 실제 분석 모듈과 가짜 조회 객체를 사용해 업로드부터 결과까지 확인함."""
    source = install_web_source(monkeypatch)
    with TestClient(app) as client:
        response = client.post("/analyze", data={"project_license": project}, files={
            "dependency_file": ("requirements.txt", b"requests==2.32.0\n", "text/plain"),
        })
    assert response.status_code == 200
    assert source.calls == ["requests", "web-dependency"]
    assert "의존성 점검 결과" in response.text
    assert "전체 2개" in response.text
    assert "직접 1개" in response.text
    assert "따라온 1개" in response.text
    assert f"프로젝트 라이선스: {project}" in response.text
    assert "2.32.0" in response.text
    assert "실제 분석은 아직 연결되지 않았습니다" not in response.text
    assert "가상 패키지" not in response.text
    assert "예시 데이터의 경고" not in response.text
    assert "법적 조언이 아닙니다" in response.text
    if project == "MIT":
        assert response.text.index("안 됨 · web-dependency") < response.text.index("써도 됨 · requests")
    else:
        assert "써도 됨 2개" in response.text

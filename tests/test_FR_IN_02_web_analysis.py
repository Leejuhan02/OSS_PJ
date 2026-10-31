"""FR-IN-02: 텍스트 입력을 분석하고 경고·조회 실패도 결과에 표시함."""

import threading

from fastapi.testclient import TestClient
from web_fakes import install_web_source

from oss_check.web.main import app
from oss_check.web.routers import pages


def test_text_analysis_keeps_line_numbers_and_runs_in_worker(monkeypatch):
    """FR-IN-02: 원문 줄 번호를 유지하고 이벤트 루프 밖에서 분석함."""
    source = install_web_source(monkeypatch)
    observed = {}
    original_analyze = pages.analyze
    original_threadpool = pages.run_in_threadpool

    def record_analysis(text, **kwargs):
        observed["text"] = text
        observed["worker"] = threading.get_ident()
        return original_analyze(text, **kwargs)

    async def record_threadpool(func, *args, **kwargs):
        observed["loop"] = threading.get_ident()
        return await original_threadpool(func, *args, **kwargs)

    monkeypatch.setattr(pages, "analyze", record_analysis)
    monkeypatch.setattr(pages, "run_in_threadpool", record_threadpool)
    text = "\nrequests\n-e .\nmissing\n"
    with TestClient(app) as client:
        response = client.post("/analyze", data={"dependency_text": text})
    assert response.status_code == 200
    assert observed["text"] == text
    assert observed["worker"] != observed["loop"]
    assert sorted(source.calls) == ["missing", "requests", "web-dependency"]
    assert "프로젝트 라이선스: MIT" in response.text
    assert "전체 3개" in response.text
    assert "조회 실패 1개" in response.text
    assert "3번째 줄" in response.text
    assert "모름 · missing" in response.text
    assert "분석 중 확인한 경고" in response.text
    assert "예시" not in response.text

"""FR-IN-08: 웹에서 1MB 초과 입력을 거부함."""

import pytest
from fastapi.testclient import TestClient

from oss_check.web.main import app
from oss_check.domain.models import Report
from oss_check.web.routers import pages


@pytest.fixture(autouse=True)
def isolate_size_check(monkeypatch):
    """크기 검사에서는 분석을 대체해 큰 문자열 해석과 외부 조회를 막음."""
    monkeypatch.setattr(pages, "analyze", lambda text, *, project, source: Report(project),
                        raising=False)


@pytest.mark.parametrize("as_file", [False, True])
@pytest.mark.parametrize("size,expected_status", [(1_048_576, 200), (1_048_577, 413)])
def test_web_input_size_boundary(as_file, size, expected_status):
    """FR-IN-08: 파일과 텍스트 모두 1MB까지 허용하고 초과는 거부함."""
    content = "a" * size
    kwargs = (
        {"files": {"dependency_file": ("requirements.txt", content.encode(), "text/plain")}}
        if as_file else {"data": {"dependency_text": content}}
    )
    with TestClient(app) as client:
        response = client.post("/analyze", **kwargs)
    assert response.status_code == expected_status
    if expected_status == 413:
        assert "입력 크기는 1MB 이하여야 합니다" in response.text
        assert "입력을 받았습니다" not in response.text


@pytest.mark.parametrize("content", ["가" * 349_526, "a" + " " * 1_048_576],
                         ids=["utf8-bytes", "trailing-spaces"])
def test_text_size_uses_original_utf8_bytes(content):
    """FR-IN-08: 글자 수나 공백 제거 후 길이가 아닌 원본 바이트를 검사함."""
    with TestClient(app) as client:
        response = client.post("/analyze", data={"dependency_text": content})
    assert response.status_code == 413
    assert "입력 크기는 1MB 이하여야 합니다" in response.text


def test_oversized_upload_is_rejected_before_disk_spooling(monkeypatch):
    """FR-IN-08: 초과 파일은 임시 디스크에 쓰기 전에 거부함."""
    from tempfile import SpooledTemporaryFile

    def reject_disk_write(self):
        raise AssertionError("업로드를 임시 디스크로 옮기면 안 됨")

    monkeypatch.setattr(SpooledTemporaryFile, "rollover", reject_disk_write)
    with TestClient(app) as client:
        response = client.post("/analyze", files={
            "dependency_file": ("requirements.txt", b"a" * 1_048_577, "text/plain"),
        })
    assert response.status_code == 413


@pytest.mark.parametrize("size,status", [(1_048_576, 200), (1_048_577, 413)])
def test_browser_multipart_text_size(size, status):
    """FR-IN-08: 브라우저의 multipart 직접 입력도 같은 제한을 적용함."""
    with TestClient(app) as client:
        response = client.post("/analyze", files={
            "dependency_text": (None, "a" * size),
            "project_license": (None, "MIT"),
        })
    assert response.status_code == status

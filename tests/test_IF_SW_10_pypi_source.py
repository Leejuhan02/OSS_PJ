import pytest
import requests
from requests.exceptions import Timeout
from oss_check.adapters.pypi_adapter import PyPIPackageSource

class MockResponse:
    def __init__(self, json_data, status_code):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(response=self)

def test_fetch_200_ok(monkeypatch):
    """정상 응답 시 info 딕셔너리 반환 및 timeout/헤더 확인"""
    def mock_get(url, **kwargs):
        assert kwargs.get("timeout") == 20
        assert kwargs.get("headers", {}).get("User-Agent") == "oss-check/0.1 (전영찬)"
        return MockResponse({"info": {"name": "requests", "version": "2.31.0"}}, 200)

    monkeypatch.setattr(requests, "get", mock_get)
    adapter = PyPIPackageSource()
    result = adapter.fetch("requests")
    assert result == {"name": "requests", "version": "2.31.0"}

def test_fetch_404_not_found(monkeypatch):
    """404 발생 시 재시도 없이 즉시 None 반환"""
    call_count = 0
    def mock_get(url, **kwargs):
        nonlocal call_count
        call_count += 1
        return MockResponse(None, 404)

    monkeypatch.setattr(requests, "get", mock_get)
    adapter = PyPIPackageSource()
    assert adapter.fetch("unknown_pkg") is None
    assert call_count == 1

def test_fetch_500_server_error(monkeypatch):
    """500 에러 발생 시 2회 재시도(총 3회 호출) 후 None 반환"""
    call_count = 0
    def mock_get(url, **kwargs):
        nonlocal call_count
        call_count += 1
        return MockResponse(None, 500)

    monkeypatch.setattr(requests, "get", mock_get)
    adapter = PyPIPackageSource()
    assert adapter.fetch("error_pkg") is None
    assert call_count == 3

def test_fetch_timeout(monkeypatch):
    """Timeout 발생 시 2회 재시도(총 3회 호출) 후 None 반환"""
    call_count = 0
    def mock_get(url, **kwargs):
        nonlocal call_count
        call_count += 1
        raise Timeout("Connection timed out")

    monkeypatch.setattr(requests, "get", mock_get)
    adapter = PyPIPackageSource()
    assert adapter.fetch("timeout_pkg") is None
    assert call_count == 3
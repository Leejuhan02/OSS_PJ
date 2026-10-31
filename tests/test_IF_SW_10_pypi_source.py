import pytest
import requests
from requests.exceptions import Timeout
from oss_check.adapters import pypi_adapter
from oss_check.adapters.pypi_adapter import PyPIPackageSource


# [강의] 테스트 패턴 — 가짜 객체
#   - monkeypatch 로 time.sleep 을 「기다린 초를 목록에 적기만 하는 함수」로 바꿈
#   - 재시도 간격·횟수는 그대로 확인하면서, 테스트가 실제로 1초씩 기다리지 않게 하려는 것임
@pytest.fixture
def waits(monkeypatch):
    recorded: list[float] = []
    monkeypatch.setattr(pypi_adapter.time, "sleep", recorded.append)
    return recorded

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
        assert kwargs.get("headers", {}).get("User-Agent") == pypi_adapter.USER_AGENT
        return MockResponse({"info": {"name": "requests", "version": "2.31.0"}}, 200)

    monkeypatch.setattr(requests, "get", mock_get)
    adapter = PyPIPackageSource()
    result = adapter.fetch("requests")
    assert result == {"name": "requests", "version": "2.31.0"}

# [강의] 테스트 패턴 — 가짜 객체
#   - requests.get 을 「받은 헤더를 기록하고 200 을 돌려주는 함수」로 바꿔, 실제로 보낼 헤더를 꺼내 봄
#   - 네트워크 없이(DC-05) 헤더 문자 문제를 잡으려는 것임. 기존 가짜 응답은 헤더를 인코딩하지 않아 이 오류를 놓쳤음
def test_user_agent_is_sendable_header(monkeypatch):
    """CR-03: User-Agent 는 프로젝트 이름과 연락처를 담고, HTTP 헤더로 보낼 수 있는 문자만 씀

    한글이 들어가면 requests 가 헤더를 latin-1 로 바꾸다 UnicodeEncodeError 가 나서 모든 조회가 실패함 (10/31 실측)
    """
    sent: dict[str, str] = {}

    def mock_get(url, **kwargs):
        sent.update(kwargs["headers"])
        return MockResponse({"info": {}}, 200)

    monkeypatch.setattr(requests, "get", mock_get)
    PyPIPackageSource().fetch("requests")
    user_agent = sent["User-Agent"]
    user_agent.encode("ascii")                         # 한글이 있으면 여기서 UnicodeEncodeError
    assert user_agent.startswith("oss-check/")         # 프로젝트 이름
    assert "https://github.com/Leejuhan02/OSS_PJ" in user_agent   # 연락처


def test_fetch_404_not_found(monkeypatch, waits):
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
    assert waits == []                                 # 404 는 재시도하지 않으므로 기다리지도 않음

def test_fetch_500_server_error(monkeypatch, waits):
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
    assert waits == [1, 1]                             # 재시도 2회 전에만 1초씩, 마지막 실패 뒤에는 기다리지 않음

def test_fetch_timeout(monkeypatch, waits):
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
    assert waits == [1, 1]

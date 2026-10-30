import time
import requests
from requests.exceptions import HTTPError, Timeout, RequestException
from oss_check.domain.ports import PackageSource  # 설계지침 §4.2: 외부 ABC 상속

def retry_pypi(func):
    """
    IF-SW-11: 5xx 에러와 타임아웃 발생 시 최대 2회 재시도 (총 3회 시도).
    FR-DEP-08: 404 및 모든 실패 상황에서는 예외 없이 None 반환.
    """
    def wrapper(*args, **kwargs):
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except HTTPError as e:
                if 500 <= e.response.status_code < 600:
                    if attempt < max_retries:
                        time.sleep(1)
                        continue
                    return None
                return None
            except Timeout:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return None
            except RequestException:
                return None
        return None
    return wrapper

class PyPIPackageSource(PackageSource):
    @retry_pypi
    def fetch(self, package_name: str) -> dict | None:
        url = f"https://pypi.org/pypi/{package_name}/json"
        
        # CR-03: 프로젝트 이름과 연락처를 User-Agent에 포함
        headers = {"User-Agent": "oss-check/0.1 (전영찬)"}
        
        # IF-SW-10: 제한 시간 20초 설정
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        return data.get("info", {})
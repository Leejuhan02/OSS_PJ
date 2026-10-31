import time
from typing import Final

import requests
from requests.exceptions import HTTPError, Timeout, RequestException
from oss_check.domain.ports import PackageSource  # 설계지침 §4.2: 외부 ABC 상속

# CR-03: 외부 요청의 User-Agent 에 프로젝트 이름과 연락처(저장소 주소)를 넣음
# [강의] 함수 어노테이션 — typing.Final
#   - 모듈 상수에 Final 을 붙여 다른 곳에서 값을 바꾸지 않는 상수임을 표시함
#   - 테스트가 이 이름을 그대로 읽어, 문구를 두 곳에 따로 적지 않게 하려는 것임
#   - HTTP 헤더는 latin-1 로 보내지므로 영문·숫자·기호만 씀. 한글이 들어가면 모든 조회가 실패함 (10/31 실측)
USER_AGENT: Final[str] = "oss-check/0.1 (+https://github.com/Leejuhan02/OSS_PJ)"

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
        
        # CR-03: 프로젝트 이름과 연락처를 User-Agent에 포함 (값은 위의 USER_AGENT)
        headers = {"User-Agent": USER_AGENT}
        
        # IF-SW-10: 제한 시간 20초 설정
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        return data.get("info", {})

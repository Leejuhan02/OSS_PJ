import functools
import time
import requests
from abc import ABC, abstractmethod

# 1. 재시도 데코레이터
def retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        attempts = 0
        while attempts < 3:
            try:
                return func(*args, **kwargs)
            except Exception:
                attempts += 1
                time.sleep(1)
        raise Exception("재시도 횟수 초과")
    return wrapper

# 2. 패키지 소스 추상 클래스 (뼈대)
class PackageSource(ABC):
    @abstractmethod
    def fetch(self, package_name: str) -> dict:
        pass

# 3. PyPI 어댑터 (PackageSource 상속 및 info 추출)
class PyPIAdapter(PackageSource):
    @retry
    def fetch(self, package_name: str) -> dict:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return data.get("info", {})

# 4. 가짜 객체 (테스트용)
class FakePackageSource(PackageSource):
    def fetch(self, package_name: str) -> dict:
        return {"name": package_name, "version": "1.0.0", "description": "가짜 데이터입니다."}
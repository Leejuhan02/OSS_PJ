import functools
import time
import requests

# 1. 데코레이터 정의
def retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        attempts = 0
        while attempts < 3:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempts += 1
                time.sleep(1)
        raise Exception("재시도 횟수 초과")
    return wrapper

# 2. Fake 객체 (테스트용)
class FakePackageSource:
    def fetch(self, name):
        return {"name": name, "version": "1.0.0", "description": "가짜 데이터입니다."}

# 3. 실제 API 호출 함수
@retry
def fetch_pypi_data(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
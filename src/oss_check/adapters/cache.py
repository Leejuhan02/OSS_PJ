from datetime import datetime, timedelta
from functools import wraps

def cache_24_hours(func):
    # 클로저: 이 데코레이터를 통과하는 함수들만 접근할 수 있는 독립된 캐시 저장소
    cache = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        # fetch(self, package_name)에서 패키지 이름 추출
        package_name = args[1] if len(args) > 1 else kwargs.get("package_name")
        
        now = datetime.now()
        # 캐시가 있고 24시간이 지나지 않았다면 네트워크 통신 없이 반환
        if package_name in cache:
            cached_data, timestamp = cache[package_name]
            if now - timestamp < timedelta(hours=24):
                return cached_data

        # 캐시에 없으면 원래 함수(fetch)를 실행하여 통신 진행
        result = func(*args, **kwargs)
        
        # 정상적인 결괏값만 현재 시간과 함께 캐시에 저장
        if result is not None:
            cache[package_name] = (result, now)
            
        return result

    # 1번 문제 해결: 테스트 파일에서 언제든 캐시를 비울 수 있도록 함수에 clear 통로를 열어둠
    wrapper.cache_clear = cache.clear
    return wrapper
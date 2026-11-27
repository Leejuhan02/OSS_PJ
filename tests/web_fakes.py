"""웹 테스트에서만 사용하는 PackageSource 대역. 외부 통신은 하지 않음."""

from oss_check.domain.ports import PackageSource


# [강의] L19 테스트 패턴 — 가짜 객체
#   - PackageSource 규격은 지키고, PyPI 대신 미리 준비한 값을 돌려준다.
#   - 외부 통신 없이 웹 입력부터 분석 결과 표시까지 확인하려고 사용한다.
class WebPackageSource(PackageSource):
    """준비한 PyPI info를 반환하며 호출한 패키지 이름을 기록함."""

    def __init__(self):
        self.calls = []

    def fetch(self, name: str) -> dict | None:
        self.calls.append(name)
        return {
            "requests": {"license_expression": "MIT", "requires_dist": ["web-dependency"]},
            "web-dependency": {"license_expression": "GPL-3.0-only", "requires_dist": []},
        }.get(name)


def install_web_source(monkeypatch):
    """웹에서 생성하는 조회 객체만 대체하고 R0·R1·R2·R3는 그대로 사용함."""
    from oss_check.web.routers import pages

    source = WebPackageSource()
    # 조회 객체만 바꿔 끼운다. 분석·식별·판정은 실제 팀 코드를 거친다.
    monkeypatch.setattr(pages, "PyPIPackageSource", lambda: source, raising=False)
    return source

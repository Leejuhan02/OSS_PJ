"""웹 테스트에서만 사용하는 PackageSource 대역. 외부 통신은 하지 않음."""

from oss_check.domain.ports import PackageSource


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
    monkeypatch.setattr(pages, "PyPIPackageSource", lambda: source, raising=False)
    return source

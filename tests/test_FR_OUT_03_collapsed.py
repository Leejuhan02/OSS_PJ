"""FR-OUT-03: 써도 됨 항목은 개수만 표시하고 기본으로 접음."""

from html.parser import HTMLParser

from fastapi.testclient import TestClient

from oss_check.web.main import app


class DetailsParser(HTMLParser):
    """접힌 영역의 속성과 안쪽 내용을 브라우저 없이 검사함."""

    def __init__(self):
        super().__init__()
        self.groups = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "details":
            self.current = {"attrs": dict(attrs), "text": ""}

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "details" and self.current is not None:
            self.groups.append(self.current)
            self.current = None


def test_allowed_packages_are_collapsed_by_default():
    """FR-OUT-03: 허용 항목만 닫힌 details에 넣고 개수를 안내함."""
    with TestClient(app) as client:
        response = client.get("/preview")
    assert response.status_code == 200
    parser = DetailsParser()
    parser.feed(response.text)
    assert len(parser.groups) == 1
    group = parser.groups[0]
    assert "open" not in group["attrs"]
    assert "써도 됨 1개" in group["text"]
    assert "sample-mit" in group["text"]
    assert "MIT: 사용 가능" in group["text"]
    for name in ("sample-gpl", "sample-missing", "sample-lgpl", "sample-unlisted"):
        assert name in response.text
        assert name not in group["text"]

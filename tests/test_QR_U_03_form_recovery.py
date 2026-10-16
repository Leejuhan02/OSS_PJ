"""QR-U-03: 오류 안내 후 사용자가 입력을 고쳐 다시 제출할 수 있음."""

import re

from fastapi.testclient import TestClient

from oss_check.web.main import app


def test_conflicting_input_keeps_text_and_license():
    """QR-U-03: 중복 입력 오류에서도 원래 텍스트와 라이선스를 유지함."""
    text = "requests==2.32.0\n  fastapi  \n"
    with TestClient(app) as client:
        response = client.post("/analyze", data={
            "dependency_text": text, "project_license": "Apache-2.0",
        }, files={"dependency_file": ("requirements.txt", b"requests", "text/plain")})
    assert response.status_code == 400
    assert f">{text}</textarea>" in response.text
    assert re.search(r'<option\s+value="Apache-2.0"\s+selected', response.text)
    assert "파일은 다시 선택해 주세요" in response.text


def test_empty_input_keeps_license_selection():
    """QR-U-03: 빈 입력 오류를 고칠 때 라이선스를 다시 고르지 않아도 됨."""
    with TestClient(app) as client:
        response = client.post("/analyze", data={"project_license": "BSD-3-Clause"})
    assert response.status_code == 400
    assert re.search(r'<option\s+value="BSD-3-Clause"\s+selected', response.text)

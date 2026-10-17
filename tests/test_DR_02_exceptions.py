"""DR-02: 기준 SPDX 예외 86종을 네트워크 없이 읽을 수 있다."""

import json
from importlib.resources import files


def test_bundled_exception_catalog():
    """DR-02: 라이선스 목록과 같은 버전의 공식 예외를 동봉한다."""
    directory = files("oss_check") / "data"
    catalog = json.loads((directory / "spdx_exceptions.json").read_text(encoding="utf-8"))
    licenses = json.loads((directory / "spdx_licenses.json").read_text(encoding="utf-8"))
    identifiers = [item["licenseExceptionId"] for item in catalog["exceptions"]]
    assert catalog["licenseListVersion"] == licenses["licenseListVersion"] == "3.29.0"
    assert len(identifiers) == len(set(identifiers)) == 86
    assert "LLVM-exception" in identifiers
    assert "Classpath-exception-2.0" in identifiers
    assert all(item["reference"].startswith("https://spdx.org/licenses/")
               for item in catalog["exceptions"])

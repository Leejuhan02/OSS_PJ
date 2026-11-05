"""DR-03: 비표준 라이선스 표기를 매핑하는 별칭 사전 테스트."""

import json
from importlib.resources import files
import pytest

from oss_check.resolve import LicenseResolver


@pytest.fixture(scope="module")
def resolver():
    return LicenseResolver()


@pytest.mark.parametrize("raw, expected", [
    ("3-Clause BSD License", "BSD-3-Clause"),
    ("2-clause BSD", "BSD-2-Clause"),
    ("Simplified BSD", "BSD-2-Clause"),
    ("MIT License (MIT)", "MIT"),
    ("The MIT License (MIT)", "MIT"),
    ("GPLv2+", "GPL-2.0-or-later"),
    ("The Unlicense (Unlicense)", "Unlicense"),
    ("ZPL 2.1", "ZPL-2.1"),
    ("License :: OSI Approved :: The Unlicense (Unlicense)", "Unlicense"),
])
def test_dr_03_verified_aliases_resolve(resolver, raw, expected):
    """DR-03: 조사·검증된 비표준 표기가 올바른 SPDX 식별자로 변환된다."""
    result = resolver.resolve({"license": raw})
    assert result.identifier == expected
    assert result.confidence == "확실"


def test_dr_03_aliases_file_integrity():
    """DR-03: 동봉된 별칭 사전의 모든 대상 ID가 유효한 SPDX ID 또는 LicenseRef이다."""
    directory = files("oss_check") / "data"
    catalog = json.loads((directory / "spdx_licenses.json").read_text(encoding="utf-8"))
    aliases = json.loads((directory / "license_aliases.json").read_text(encoding="utf-8"))
    valid_ids = {item["licenseId"] for item in catalog["licenses"]}

    for name, target in aliases.items():
        assert target in valid_ids or target.startswith("LicenseRef-"), (
            f"유효하지 않은 SPDX 식별자: {name} -> {target}"
        )

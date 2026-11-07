"""DR-03: 사전 50개·정규화 후 40개 이상과 검증된 버전별 별칭을 보장한다."""

import json
from importlib.resources import files

import pytest

from oss_check.resolve import LicenseResolver, identify
from oss_check.resolve.metadata import normalize_license_name


# PyPI AT-1 응답, 공식 classifier 목록, SPDX 버전별 식별자를 대조한 기대값.
NEW_ALIASES = [
    ("GNU GPLv3+", "GPL-3.0-or-later"),
    ("GNU General Public License v3 or later (GPLv3+)", "GPL-3.0-or-later"),
    ("GNU General Public License v2 or later (GPLv2+)", "GPL-2.0-or-later"),
    ("GNU Lesser General Public License v3 or later (LGPLv3+)", "LGPL-3.0-or-later"),
    ("GNU Affero General Public License v3 or later (AGPLv3+)", "AGPL-3.0-or-later"),
    ("GNU General Public License v2 (GPLv2)", "GPL-2.0-only"),
    ("GNU General Public License v3 (GPLv3)", "GPL-3.0-only"),
    ("GNU Lesser General Public License v2 (LGPLv2)", "LGPL-2.0-only"),
    ("GNU Lesser General Public License v3 (LGPLv3)", "LGPL-3.0-only"),
    ("GNU Affero General Public License v3", "AGPL-3.0-only"),
    ("GPLv3+", "GPL-3.0-or-later"),
    ("GNU GPLv2+", "GPL-2.0-or-later"),
    ("LGPLv2.1+", "LGPL-2.1-or-later"),
    ("LGPLv3+", "LGPL-3.0-or-later"),
    ("AGPLv3+", "AGPL-3.0-or-later"),
    ("Modified BSD License", "BSD-3-Clause"),
    ("New BSD License", "BSD-3-Clause"),
    ("Revised BSD License", "BSD-3-Clause"),
    ("BSD 2-Clause License (FreeBSD/Simplified)", "BSD-2-Clause"),
    ("BSD 3-Clause License (Revised)", "BSD-3-Clause"),
    ("Mozilla Public License 1.1 (MPL 1.1)", "MPL-1.1"),
    ("Zope Public License 2.1 (ZPL 2.1)", "ZPL-2.1"),
]


def test_bundled_dictionary_meets_required_size_without_case_padding():
    """DR-03: 원문 키 50개와 정규화 후 서로 다른 별칭 40개 이상을 확보한다."""
    path = files("oss_check") / "data" / "license_aliases.json"
    aliases = json.loads(path.read_text(encoding="utf-8"))
    assert len(aliases) >= 50
    assert len({normalize_license_name(name) for name in aliases}) >= 40
    # 유효하지 않은 대상·동일 정규화 키의 상충 매핑은 생성자에서 거부해야 한다.
    LicenseResolver()


@pytest.mark.parametrize("raw,expected", NEW_ALIASES)
@pytest.mark.parametrize("field", ["license_expression", "license", "classifiers"])
def test_versioned_alias_mapping_and_confidence(raw, expected, field):
    """DR-03: 명시된 버전과 +를 보존하고 classifier만 추정으로 기록한다."""
    value = [f"License :: OSI Approved :: {raw}"] if field == "classifiers" else raw
    result = identify("alias-pkg", {field: value})
    assert result.options == (frozenset({expected}),)
    assert result.origin == field
    assert result.confidence == ("추정" if field == "classifiers" else "확실")
    assert result.raw == (value[0] if isinstance(value, list) else raw)


@pytest.mark.parametrize("raw", [
    "BSD License", "GPL License", "Apache License", "GNU General Public License (GPL)",
    "GNU Library or Lesser General Public License (LGPL)",
])
def test_unspecified_versions_stay_unknown(raw):
    """DR-03: BSD 조항 수·GPL 버전이 없는 일반 명칭을 임의로 확정하지 않는다."""
    result = identify("pkg", {"license": raw})
    assert result.options is None
    assert (result.confidence, result.raw) == ("미상", raw)

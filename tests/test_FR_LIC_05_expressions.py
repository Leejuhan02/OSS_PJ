"""FR-LIC-05: 괄호 없는 SPDX 식 전체를 해석하고 깨진 식은 부분 수용하지 않는다."""

import pytest

from oss_check.resolve import identify


@pytest.mark.parametrize("raw", [
    "MIT OR GPL-3.0-only", "MIT AND Apache-2.0",
    "Apache-2.0 WITH LLVM-exception", "GPL-2.0-only WITH Classpath-exception-2.0",
    "MIT\nOR GPL-3.0-only", "MIT OR Apache-2.0 AND BSD-3-Clause",
])
def test_complete_expression_is_identified(raw):
    """FR-LIC-05: 유효한 식은 하위 필드로 넘어가지 않고 원문을 보존한다."""
    result = identify("pkg", {"license_expression": raw, "license": "ISC"})
    assert result.confidence == "확실"
    assert result.origin == "license_expression"
    assert result.raw == raw


def test_with_returns_base_license_only():
    """FR-LIC-05: SRS 회귀 기준대로 예외는 원문에, 기본 ID는 선택지에 남긴다."""
    result = identify("pkg", {"license_expression": "Apache-2.0 WITH LLVM-exception"})
    assert result.options == (frozenset({"Apache-2.0"}),)


@pytest.mark.parametrize("raw", [
    "MIT AND UNKNOWN", "UNKNOWN OR MIT", "MIT OR", "OR MIT", "MIT AND AND Apache-2.0",
    "MIT WITH", "WITH LLVM-exception", "MIT WITH Unknown-exception",
    "MIT WITH LLVM-exception WITH Classpath-exception-2.0",
    "MIT OR (Apache-2.0 AND BSD-3-Clause)", "MIT AND ()", "MIT, GPL-3.0-only",
    "MIT WITH LLVM-exception trailing", "MIT AND OR Apache-2.0",
])
def test_invalid_expression_falls_back_without_partial_success(raw):
    """FR-LIC-05: 일부 ID만 골라 성공시키지 않고 다음 필드로 이동한다."""
    result = identify("pkg", {"license_expression": raw, "license": "ISC"})
    assert result.options == (frozenset({"ISC"}),)
    assert result.origin == "license"
    assert identify("pkg", {"license_expression": raw}).options is None


def test_legacy_expression_keeps_original_text_and_length_limit():
    """FR-LIC-05: legacy 첫 줄 해석과 FR-LIC-02의 200자 제한을 유지한다."""
    raw = "MIT OR Apache-2.0\nCopyright example"
    assert identify("pkg", {"license": raw}).raw == raw
    assert identify("pkg", {"license": raw}).confidence == "확실"
    assert identify("pkg", {"license": raw + "x" * 201}).options is None


@pytest.mark.parametrize("field", ["license_expression", "license"])
def test_official_name_with_or_is_not_split_as_an_operator(field):
    """FR-LIC-05: 공식 라이선스 이름에 들어 있는 or를 연산자로 오인하지 않는다."""
    raw = "GNU General Public License v3.0 or later"
    result = identify("pkg", {field: raw})
    assert result.options == (frozenset({"GPL-3.0-or-later"}),)
    assert result.raw == raw

"""FR-LIC-07: 등록된 라이선스 이름 속 or later와 실제 연산자를 구별한다."""

import pytest

from oss_check.resolve import identify


NAME = "GNU General Public License v3.0 or later"


@pytest.mark.parametrize("raw,choices", [
    (f"{NAME} AND MIT", ({"GPL-3.0-or-later", "MIT"},)),
    (f"MIT AND {NAME}", ({"GPL-3.0-or-later", "MIT"},)),
    (f"{NAME} OR MIT", ({"GPL-3.0-or-later"}, {"MIT"})),
    (f"MIT OR {NAME}", ({"MIT"}, {"GPL-3.0-or-later"})),
    (f"{NAME} WITH Classpath-exception-2.0 AND MIT", ({"GPL-3.0-or-later", "MIT"},)),
    (f"  {NAME.swapcase().replace(' ', '  ')} and MIT  ", ({"GPL-3.0-or-later", "MIT"},)),
])
def test_registered_name_is_one_operand(raw, choices):
    """FR-LIC-07: 알려진 이름은 한 피연산자로 보존하고 바깥 연산자만 적용한다."""
    result = identify("pkg", {"license_expression": raw})
    assert result.options == tuple(frozenset(choice) for choice in choices)
    assert result.raw == raw
    assert (result.origin, result.confidence) == ("license_expression", "확실")


@pytest.mark.parametrize("raw", [
    f"{NAME} OR", f"{NAME} AND Unknown permission", f"Unknown {NAME} OR MIT",
    f"{NAME} extra words OR MIT", f"({NAME} OR MIT)",
    f"{NAME} WITH Unknown-exception OR MIT",
])
def test_name_matching_does_not_hide_invalid_terms(raw):
    """FR-LIC-07: 이름 일부·불완전식·미지원 괄호는 전체 실패 후 폴백한다."""
    result = identify("pkg", {"license_expression": raw, "license": "Apache-2.0"})
    assert result.options == (frozenset({"Apache-2.0"}),)
    assert result.origin == "license"

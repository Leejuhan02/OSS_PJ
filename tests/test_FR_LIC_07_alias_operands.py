"""FR-LIC-07: 기존 별칭을 피연산자로 변환하고 식의 의미와 공개 계약을 보존한다."""

import json
from importlib.resources import files

import pytest

from oss_check.resolve import identify
from oss_check.resolve.metadata import LicenseResolver


ALIASES = json.loads((files("oss_check") / "data" / "license_aliases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("alias,target", ALIASES.items())
@pytest.mark.parametrize("field", ["license_expression", "license"])
@pytest.mark.parametrize("operator", ["AND", "OR", "WITH"])
def test_each_bundled_alias_as_operand(alias, target, field, operator):
    """FR-LIC-07: 모든 기존 별칭을 두 필드의 AND·OR·WITH 피연산자로 확인한다."""
    raw = f"{alias} WITH LLVM-exception" if operator == "WITH" else f"{alias} {operator} MIT"
    choices = ({target}, {"MIT"}) if operator == "OR" else ({target, "MIT"},)
    if operator == "WITH":
        choices = ({target},)
    expected = tuple(dict.fromkeys(frozenset(choice) for choice in choices))
    result = identify("alias-pkg", {field: raw})
    assert result.options == expected
    assert (result.package, result.origin, result.raw, result.confidence) == (
        "alias-pkg", field, raw, "확실")


@pytest.mark.parametrize("raw,choices", [
    ("BSD 3-Clause OR Apache-2.0", ({"BSD-3-Clause"}, {"Apache-2.0"})),
    ("MIT AND BSD 3-Clause", ({"MIT", "BSD-3-Clause"},)),
    ("MIT OR ISC License (ISCL)", ({"MIT"}, {"ISC"})),
    ("Apache 2 WITH LLVM-exception AND BSD-3 OR MIT licence", ({"Apache-2.0", "BSD-3-Clause"}, {"MIT"})),
    ("  bSd   3-Clause licence\tand\tAPACHE 2.0  ", ({"BSD-3-Clause", "Apache-2.0"},)),
    ("BSD 3-Clause OR BSD-3", ({"BSD-3-Clause"},)),
])
def test_mixed_operands_normalization_and_deduplication(raw, choices):
    """FR-LIC-07: SRS 예시·오른쪽 별칭·우선순위·정규화·중복 제거를 확인한다."""
    result = identify("pkg", {"license_expression": raw, "license": "GPL-3.0-only"})
    assert result.options == tuple(frozenset(choice) for choice in choices)
    assert result.origin == "license_expression"
    assert result.raw == raw


@pytest.mark.parametrize("raw", [
    "BSD License OR MIT", "BSD 3-Clause AND Unknown terms", "BSD 3-Clause OR",
    "BSD 3-Clause WITH Unknown-exception", "(BSD 3-Clause OR MIT)",
    "BSD 3-Clause AND (MIT OR Apache-2.0)", "ISC License (ISCL) AND ()",
    "ISC License (ISCL OR MIT", "ISC License (ISCL) OR MIT)",
    "ISC License (ISCL) AND (MIT OR Apache-2.0)", "BSD 3-Clause AND MIT ()",
])
def test_invalid_alias_expression_falls_back_as_a_whole(raw):
    """FR-LIC-07: 미상 표기·깨진 식·그룹 괄호를 부분 성공시키지 않는다."""
    result = identify("pkg", {"license_expression": raw, "license": "Apache 2"})
    assert result.options == (frozenset({"Apache-2.0"}),)
    assert result.origin == "license"
    unknown = identify("pkg", {"license_expression": raw})
    assert unknown.options is None
    assert unknown.confidence == "미상"
    assert unknown.raw == raw


def test_replaced_dictionary_is_used_for_compound_operands(tmp_path):
    """FR-LIC-07: 동봉 사전 확장 없이 교체 사전도 복합식에 적용되는지 확인한다."""
    catalog = {"licenses": [{"licenseId": "MIT", "name": "MIT License"}]}
    (tmp_path / "spdx_licenses.json").write_text(json.dumps(catalog), encoding="utf-8")
    alias_path = tmp_path / "license_aliases.json"
    alias_path.write_text(json.dumps({"Team permission": "MIT"}), encoding="utf-8")
    raw = "Team permission AND MIT"
    assert LicenseResolver(tmp_path).resolve({"license_expression": raw}).options == (frozenset({"MIT"}),)
    alias_path.write_text(json.dumps({"Team permission": "LicenseRef-Internal"}), encoding="utf-8")
    result = LicenseResolver(tmp_path).resolve({"license_expression": raw})
    assert result.options == (frozenset({"LicenseRef-Internal", "MIT"}),)


def test_alias_failure_reaches_classifier_and_preserves_confidence():
    """FR-LIC-07: 두 식 필드 실패 후 classifier의 추정 계약을 유지한다."""
    result = identify("pkg", {"license_expression": "BSD 3-Clause AND Unknown terms",
                              "license": "ISC License (ISCL) OR",
                              "classifiers": ["License :: OSI Approved :: Apache Software License"]})
    assert result.options == (frozenset({"Apache-2.0"}),)
    assert (result.origin, result.confidence) == ("classifiers", "추정")


@pytest.mark.parametrize("alias,target", ALIASES.items())
def test_alias_on_right_with_normalized_spelling(alias, target):
    """FR-LIC-07: 오른쪽 피연산자도 대소문자·공백 정규화 후 같은 ID로 변환한다."""
    spelling = "  ".join(alias.swapcase().split())
    raw = f"MIT and {spelling}"
    assert identify("pkg", {"license_expression": raw}).options == (frozenset({"MIT", target}),)


def test_alias_url_and_legacy_first_line_keep_raw():
    """FR-LIC-07: URL 제거와 legacy 첫 줄 규칙을 적용해도 원문은 보존한다."""
    raw = "BSD 3-Clause https://example.invalid/bsd OR Apache 2\nCopyright example"
    result = identify("pkg", {"license": raw})
    assert result.options == (frozenset({"BSD-3-Clause"}), frozenset({"Apache-2.0"}))
    assert result.raw == raw
    assert result.origin == "license"


def test_alias_legacy_length_boundary():
    """FR-LIC-07: 별칭 식도 legacy 200자 제한을 우회하지 않는다."""
    raw = "BSD 3-Clause OR Apache 2"
    raw = raw.ljust(200)
    assert identify("pkg", {"license": raw}).options is not None
    assert identify("pkg", {"license": raw + " "}).options is None


def test_real_pipeline_receives_alias_choices():
    """FR-LIC-07: 가짜 조회를 사용한 실제 분석 연결에 별칭의 ID 구조를 전달한다."""
    from app_fakes import CountingSource
    from oss_check.app.service import analyze

    source = CountingSource({"root": {"license_expression": "BSD 3-Clause OR Apache 2",
                                     "requires_dist": ["dep"]},
                             "dep": {"license": "ISC License (ISCL) AND MIT licence"}})
    report = analyze("root", project="MIT", source=source)
    rows = {row.package.name: row for row in report.rows}
    assert rows["root"].license.options == (frozenset({"BSD-3-Clause"}), frozenset({"Apache-2.0"}))
    assert rows["dep"].license.options == (frozenset({"ISC", "MIT"}),)
    assert source.calls == {"root": 1, "dep": 1}

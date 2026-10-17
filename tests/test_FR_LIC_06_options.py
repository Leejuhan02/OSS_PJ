"""FR-LIC-06: OR 선택지와 AND 동시 적용을 공통 모델에 보존한다."""

import pytest

from oss_check.resolve import identify


@pytest.mark.parametrize("raw,choices", [
    ("MIT OR Apache-2.0", ({"MIT"}, {"Apache-2.0"})),
    ("MIT AND Apache-2.0", ({"MIT", "Apache-2.0"},)),
    ("MIT OR Apache-2.0 AND BSD-3-Clause", ({"MIT"}, {"Apache-2.0", "BSD-3-Clause"})),
    ("MIT AND Apache-2.0 OR BSD-3-Clause", ({"MIT", "Apache-2.0"}, {"BSD-3-Clause"})),
    ("Apache-2.0 WITH LLVM-exception AND MIT OR ISC", ({"Apache-2.0", "MIT"}, {"ISC"})),
    ("MIT AND MIT", ({"MIT"},)),
    ("MIT OR MIT", ({"MIT"},)),
    ("MIT AND Apache-2.0 OR Apache-2.0 AND MIT", ({"MIT", "Apache-2.0"},)),
    ("LicenseRef-Company OR MIT", ({"LicenseRef-Company"}, {"MIT"})),
    ("mit\tand APACHE-2.0\nor ISC", ({"MIT", "Apache-2.0"}, {"ISC"})),
])
def test_options_preserve_expression_meaning(raw, choices):
    """FR-LIC-06: 선택지 순서를 유지하고 의미가 같은 선택지는 중복하지 않는다."""
    result = identify("pkg", {"license_expression": raw})
    assert result.options == tuple(frozenset(choice) for choice in choices)
    assert result.raw == raw
    assert result.package == "pkg"


def test_compound_legacy_fallback_preserves_confidence_and_origin():
    """FR-LIC-06: 깨진 상위 필드 후 legacy 복합식도 선택지를 보존한다."""
    result = identify("pkg", {"license_expression": "MIT AND UNKNOWN",
                              "license": "MIT OR GPL-3.0-only"})
    assert result.options == (frozenset({"MIT"}), frozenset({"GPL-3.0-only"}))
    assert result.origin == "license"
    assert result.confidence == "확실"


def test_real_pipeline_receives_compound_choices_and_keeps_lookup_failure():
    """FR-LIC-06: 실제 조정자·판정에 선택지를 전달하고 조회 실패를 구별한다."""
    from app_fakes import CountingSource
    from oss_check.app.service import analyze

    source = CountingSource({
        "root": {"license_expression": "MIT OR GPL-3.0-only", "requires_dist": ["dep", "ghost"]},
        "dep": {"license_expression": "MIT AND GPL-3.0-only"},
    })
    report = analyze("root", project="MIT", source=source)
    rows = {row.package.name: row for row in report.rows}
    assert rows["root"].license.options == (frozenset({"MIT"}), frozenset({"GPL-3.0-only"}))
    assert rows["root"].judgement.verdict == "써도 됨"
    assert rows["dep"].license.options == (frozenset({"MIT", "GPL-3.0-only"}),)
    assert rows["dep"].judgement.verdict == "안 됨"
    assert rows["ghost"].package.lookup_failed
    assert report.counts()["failed"] == 1
    assert source.calls == {"root": 1, "dep": 1, "ghost": 1}

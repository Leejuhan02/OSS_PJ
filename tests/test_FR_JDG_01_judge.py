"""
FR-JDG 판정 알고리즘 동작 검증을 위한 정답셋 테스트
"""

import pytest
from oss_check.domain.models import LicenseInfo, Judgement
from oss_check.judge.judge_logic import judge


# 1. 테스트에 사용할 가짜 LicenseInfo 생성 헬퍼 함수
def make_lic(name: str, options: tuple[frozenset[str], ...] | None) -> LicenseInfo:
    if options is None:
        return LicenseInfo.unknown(name)
    return LicenseInfo(
        package=name,
        options=options,
        confidence="확실",
        origin="license_expression",
        raw="test-raw",
    )


# 2. 정답셋(Ground Truth) 정의
TEST_GROUND_TRUTH = [
    # (패키지명, options, 프로젝트_라이선스, 기대_verdict, 기대_decisive_license)
    (
        "proprietary-pkg",
        (frozenset({"LicenseRef-Private"}),),
        "MIT",
        "안 됨",
        "LicenseRef-Private",
    ),
    (
        "unknown-pkg",
        None,
        "MIT",
        "모름",
        None,
    ),
    (
        "unregistered-pkg",
        (frozenset({"Custom-Open-1.0"}),),
        "MIT",
        "판단보류",
        None,
    ),
    (
        "lgpl-pkg",
        (frozenset({"LGPL-2.1-only"}),),
        "MIT",
        "조건 있음",
        "LGPL-2.1-only",
    ),
    (
        "gpl-pkg",
        (frozenset({"GPL-3.0-only"}),),
        "MIT",
        "안 됨",
        "GPL-3.0-only",
    ),
    (
        "or-condition-pkg",
        (frozenset({"GPL-3.0-only"}), frozenset({"MIT"})),
        "MIT",
        "써도 됨",
        "MIT",
    ),
    (
        "and-condition-pkg",
        (frozenset({"MIT", "GPL-3.0-only"}),),
        "MIT",
        "안 됨",
        "GPL-3.0-only",
    ),
]


@pytest.mark.parametrize(
    "pkg_name, options, project, expected_verdict, expected_decisive",
    TEST_GROUND_TRUTH,
)
def test_judge_ground_truth(
    pkg_name: str,
    options: tuple[frozenset[str], ...] | None,
    project: str,
    expected_verdict: str,
    expected_decisive: str | None,
):
    """FR-JDG: 정답셋을 통한 판정 알고리즘 결과 검증"""
    lic = make_lic(pkg_name, options)
    
    # 판정 실행
    result: Judgement = judge(lic, project=project)

    # 검증
    assert result.verdict == expected_verdict
    assert result.decisive_license == expected_decisive
    assert result.reason != ""  # FR-JDG-10: 사유는 항상 비어있지 않아야 함
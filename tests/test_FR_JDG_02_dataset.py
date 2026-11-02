"""
FR-JDG 판정 알고리즘 대용량 정답 데이터셋 (Ground Truth Dataset)
- 다양한 내 프로젝트 라이선스(MIT, Apache-2.0, BSD-3-Clause, GPL-3.0-only, AGPL-3.0-only 등)
- 단일, OR 복합, AND 복합, 독점, 미상, 등급표 미등록 라이선스 전 케이스 커버
"""

import pytest
from oss_check.domain.models import LicenseInfo, Judgement
from oss_check.judge.judge_logic import judge


# 정답 데이터셋 (25개 시나리오)
GROUND_TRUTH_DATASET = [
    # 그룹 1: 독점 / 미상 / 등급표 미등록 라이선스 (FR-JDG-07, 08, 09, 11)
    (
        "독점 라이선스 식별자 (LicenseRef-Private)",
        LicenseInfo("proprietary-pkg", (frozenset({"LicenseRef-Private"}),), "확실", "license_expression", "LicenseRef-Private"),
        "MIT",
        "안 됨",
        "LicenseRef-Private",
    ),
    (
        "독점 라이선스 식별자 대소문자 혼용 (licenseref-custom)",
        LicenseInfo("custom-proprietary", (frozenset({"licenseref-custom"}),), "확실", "license_expression", "licenseref-custom"),
        "GPL-3.0-only",
        "안 됨",
        "licenseref-custom",
    ),
    (
        "라이선스 정보 없음 (options=None) -> 모름",
        LicenseInfo.unknown("unknown-pkg"),
        "Apache-2.0",
        "모름",
        None,
    ),
    (
        "등급표(tiers.json) 미등록 커스텀 라이선스 -> 판단보류",
        LicenseInfo("custom-open-pkg", (frozenset({"Custom-Open-1.0"}),), "확실", "license_expression", "Custom-Open-1.0"),
        "BSD-3-Clause",
        "판단보류",
        None,
    ),

    # 그룹 2: Permissive (Tier 1) 내 프로젝트 라이선스 (MIT, Apache-2.0, BSD-3-Clause)
    (
        "[MIT 프로젝트] Permissive (Apache-2.0, Tier 1) -> 써도 됨",
        LicenseInfo("urllib3", (frozenset({"Apache-2.0"}),), "확실", "license_expression", "Apache-2.0"),
        "MIT",
        "써도 됨",
        "Apache-2.0",
    ),
    (
        "[MIT 프로젝트] Weak Copyleft (LGPL-2.1-only, Tier 2) -> 조건 있음",
        LicenseInfo("certifi-lgpl", (frozenset({"LGPL-2.1-only"}),), "확실", "license_expression", "LGPL-2.1-only"),
        "MIT",
        "조건 있음",
        "LGPL-2.1-only",
    ),
    (
        "[MIT 프로젝트] Weak Copyleft (MPL-2.0, Tier 2) -> 조건 있음",
        LicenseInfo("certifi-mpl", (frozenset({"MPL-2.0"}),), "확실", "license_expression", "MPL-2.0"),
        "MIT",
        "조건 있음",
        "MPL-2.0",
    ),
    (
        "[MIT 프로젝트] Strong Copyleft (GPL-3.0-only, Tier 3) -> 안 됨",
        LicenseInfo("gpl-pkg", (frozenset({"GPL-3.0-only"}),), "확실", "license_expression", "GPL-3.0-only"),
        "MIT",
        "안 됨",
        "GPL-3.0-only",
    ),
    (
        "[MIT 프로젝트] Network Copyleft (AGPL-3.0-only, Tier 4) -> 안 됨",
        LicenseInfo("agpl-pkg", (frozenset({"AGPL-3.0-only"}),), "확실", "license_expression", "AGPL-3.0-only"),
        "MIT",
        "안 됨",
        "AGPL-3.0-only",
    ),
    (
        "[Apache-2.0 프로젝트] Permissive (BSD-3-Clause, Tier 1) -> 써도 됨",
        LicenseInfo("numpy", (frozenset({"BSD-3-Clause"}),), "확실", "license_expression", "BSD-3-Clause"),
        "Apache-2.0",
        "써도 됨",
        "BSD-3-Clause",
    ),
    (
        "[Apache-2.0 프로젝트] Weak Copyleft (LGPL-3.0-only, Tier 2) -> 조건 있음",
        LicenseInfo("lgpl3-pkg", (frozenset({"LGPL-3.0-only"}),), "확실", "license_expression", "LGPL-3.0-only"),
        "Apache-2.0",
        "조건 있음",
        "LGPL-3.0-only",
    ),
    (
        "[BSD-3-Clause 프로젝트] Strong Copyleft (GPL-2.0-only, Tier 3) -> 안 됨",
        LicenseInfo("gpl2-pkg", (frozenset({"GPL-2.0-only"}),), "확실", "license_expression", "GPL-2.0-only"),
        "BSD-3-Clause",
        "안 됨",
        "GPL-2.0-only",
    ),

    # 그룹 3: Copyleft (Tier 2, 3, 4) 내 프로젝트 라이선스 (LGPL, GPL, AGPL)
    (
        "[LGPL-2.1-only 프로젝트] Permissive (MIT, Tier 1) -> 써도 됨",
        LicenseInfo("requests", (frozenset({"MIT"}),), "확실", "license_expression", "MIT"),
        "LGPL-2.1-only",
        "써도 됨",
        "MIT",
    ),
    (
        "[LGPL-2.1-only 프로젝트] 동급 Weak Copyleft (MPL-2.0, Tier 2) -> 써도 됨",
        LicenseInfo("mpl-lib", (frozenset({"MPL-2.0"}),), "확실", "license_expression", "MPL-2.0"),
        "LGPL-2.1-only",
        "써도 됨",
        "MPL-2.0",
    ),
    (
        "[LGPL-2.1-only 프로젝트] Strong Copyleft (GPL-3.0-only, Tier 3) -> 안 됨",
        LicenseInfo("gpl-tool", (frozenset({"GPL-3.0-only"}),), "확실", "license_expression", "GPL-3.0-only"),
        "LGPL-2.1-only",
        "안 됨",
        "GPL-3.0-only",
    ),
    (
        "[GPL-3.0-only 프로젝트] Permissive (Apache-2.0, Tier 1) -> 써도 됨",
        LicenseInfo("apache-lib", (frozenset({"Apache-2.0"}),), "확실", "license_expression", "Apache-2.0"),
        "GPL-3.0-only",
        "써도 됨",
        "Apache-2.0",
    ),
    (
        "[GPL-3.0-only 프로젝트] Weak Copyleft (LGPL-3.0-only, Tier 2) -> 써도 됨",
        LicenseInfo("lgpl-lib", (frozenset({"LGPL-3.0-only"}),), "확실", "license_expression", "LGPL-3.0-only"),
        "GPL-3.0-only",
        "써도 됨",
        "LGPL-3.0-only",
    ),
    (
        "[GPL-3.0-only 프로젝트] 동급 Strong Copyleft (GPL-3.0-only, Tier 3) -> 써도 됨",
        LicenseInfo("gpl-lib", (frozenset({"GPL-3.0-only"}),), "확실", "license_expression", "GPL-3.0-only"),
        "GPL-3.0-only",
        "써도 됨",
        "GPL-3.0-only",
    ),
    (
        "[GPL-3.0-only 프로젝트] Network Copyleft (AGPL-3.0-only, Tier 4) -> 안 됨",
        LicenseInfo("agpl-tool", (frozenset({"AGPL-3.0-only"}),), "확실", "license_expression", "AGPL-3.0-only"),
        "GPL-3.0-only",
        "안 됨",
        "AGPL-3.0-only",
    ),

    # 그룹 4: 복합 조건 (OR / AND) 판정 (FR-JDG-03, FR-JDG-04)
    (
        "OR 조건 (GPL-3.0-only OR MIT) -> [MIT 프로젝트] 약한 조건 MIT 선택 -> 써도 됨",
        LicenseInfo("dual-pkg-1", (frozenset({"GPL-3.0-only"}), frozenset({"MIT"})), "확실", "license_expression", "GPL-3.0-only OR MIT"),
        "MIT",
        "써도 됨",
        "MIT",
    ),
    (
        "OR 조건 (AGPL-3.0-only OR LGPL-2.1-only) -> [Apache-2.0 프로젝트] 약한 조건 LGPL 선택 -> 조건 있음",
        LicenseInfo("dual-pkg-2", (frozenset({"AGPL-3.0-only"}), frozenset({"LGPL-2.1-only"})), "확실", "license_expression", "AGPL-3.0-only OR LGPL-2.1-only"),
        "Apache-2.0",
        "조건 있음",
        "LGPL-2.1-only",
    ),
    (
        "AND 조건 (MIT AND GPL-3.0-only) -> [MIT 프로젝트] 강한 조건 GPL 적용 -> 안 됨",
        LicenseInfo("multi-pkg-1", (frozenset({"MIT", "GPL-3.0-only"}),), "확실", "license_expression", "MIT AND GPL-3.0-only"),
        "MIT",
        "안 됨",
        "GPL-3.0-only",
    ),
    (
        "AND 조건 (MIT AND LGPL-2.1-only) -> [Apache-2.0 프로젝트] 강한 조건 LGPL 적용 -> 조건 있음",
        LicenseInfo("multi-pkg-2", (frozenset({"MIT", "LGPL-2.1-only"}),), "확실", "license_expression", "MIT AND LGPL-2.1-only"),
        "Apache-2.0",
        "조건 있음",
        "LGPL-2.1-only",
    ),
    (
        "AND 조건 (Apache-2.0 AND BSD-3-Clause) -> [MIT 프로젝트] 둘 다 Tier 1 -> 써도 됨",
        LicenseInfo("multi-pkg-3", (frozenset({"Apache-2.0", "BSD-3-Clause"}),), "확실", "license_expression", "Apache-2.0 AND BSD-3-Clause"),
        "MIT",
        "써도 됨",
        "BSD-3-Clause",  # 동일 Tier(Tier 1) 동점 시 알파벳순 비교 결과에 맞춰 수정
    ),
    (
        "복합 조건 ( (MIT AND GPL-3.0) OR Apache-2.0 ) -> [MIT 프로젝트] 더 유연한 Apache-2.0 선택 -> 써도 됨",
        LicenseInfo("complex-pkg", (frozenset({"MIT", "GPL-3.0-only"}), frozenset({"Apache-2.0"})), "확실", "license_expression", "(MIT AND GPL-3.0-only) OR Apache-2.0"),
        "MIT",
        "써도 됨",
        "Apache-2.0",
    ),
]


# Pytest 함수
@pytest.mark.parametrize(
    "desc, lic, project, expected_verdict, expected_decisive",
    GROUND_TRUTH_DATASET,
)
def test_judge_ground_truth_extended(
    desc: str,
    lic: LicenseInfo,
    project: str,
    expected_verdict: str,
    expected_decisive: str | None,
):
    """FR-JDG: 대용량 정답 데이터셋을 통한 판정 알고리즘 검증"""
    result: Judgement = judge(lic, project=project)

    assert result.verdict == expected_verdict, f"[{desc}] 판정 결과 오류: {result.verdict} != {expected_verdict}"
    assert result.decisive_license == expected_decisive, f"[{desc}] 결정적 라이선스 오류: {result.decisive_license} != {expected_decisive}"
    assert result.reason != "", f"[{desc}] 사유(reason) 필드가 비어있음"
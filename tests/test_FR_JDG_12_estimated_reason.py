"""FR-JDG-12: 추정 판정 사유에 신뢰 수준 표시 검증."""

from oss_check.domain.models import LicenseInfo
from oss_check.judge.judge_logic import judge


def test_estimated_license_reason_mentions_estimation():
    license_info = LicenseInfo.single(
        "estimated-package",
        "MIT",
        confidence="추정",
        origin="classifiers",
    )

    result = judge(license_info, project="MIT")

    assert "추정" in result.reason

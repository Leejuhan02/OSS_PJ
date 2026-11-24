"""FR-JDG: JSON 정답 데이터셋 검증."""

import json
from importlib.resources import files

import pytest
from oss_check.domain.models import LicenseInfo, Judgement
from oss_check.judge.judge_logic import judge


def load_judge_test_cases() -> list[tuple[str, LicenseInfo, str, str, str | None, str | None]]:
    data_file = files("oss_check") / "data" / "judge_test_cases.json"
    with data_file.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    dataset = []
    for case in cases:
        license_data = case["license"]
        raw_options = license_data["options"]
        options = None if raw_options is None else tuple(
            frozenset(choice) for choice in raw_options
        )
        lic = LicenseInfo(
            package=license_data["package"],
            options=options,
            confidence=license_data["confidence"],
            origin=license_data["origin"],
            raw=license_data["raw"],
        )
        dataset.append((
            case["description"],
            lic,
            case["project"],
            case["expected_verdict"],
            case["expected_decisive_license"],
            case["expected_reason_contains"],
        ))
    return dataset


JUDGE_TEST_CASES = load_judge_test_cases()


@pytest.mark.parametrize(
    "desc, lic, project, expected_verdict, expected_decisive, expected_reason_contains",
    JUDGE_TEST_CASES,
)
def test_judge_test_cases(
    desc: str,
    lic: LicenseInfo,
    project: str,
    expected_verdict: str,
    expected_decisive: str | None,
    expected_reason_contains: str | None,
):
    """FR-JDG: 대용량 정답 데이터셋을 통한 판정 알고리즘 검증"""
    result: Judgement = judge(lic, project=project)

    assert result.verdict == expected_verdict, f"[{desc}] 판정 결과 오류: {result.verdict} != {expected_verdict}"
    assert result.decisive_license == expected_decisive, f"[{desc}] 결정적 라이선스 오류: {result.decisive_license} != {expected_decisive}"
    assert result.reason != "", f"[{desc}] 사유(reason) 필드가 비어있음"
    if expected_reason_contains is not None:
        assert expected_reason_contains in result.reason, (
            f"[{desc}] 사유에 {expected_reason_contains!r}가 없음"
        )
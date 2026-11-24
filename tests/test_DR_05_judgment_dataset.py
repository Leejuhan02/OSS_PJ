"""DR-05: 판정 정답셋 JSON이 필수 사례 수를 충족하는지 검증."""

import json
from importlib.resources import files


def test_judgment_test_cases_has_at_least_30_cases():
    data_file = files("oss_check") / "data" / "judge_test_cases.json"
    with data_file.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    assert len(cases) >= 30

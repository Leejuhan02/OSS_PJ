# [강의] L05 FCF 디자인 패턴 / L06 사용자 정의 Callable (__call__) / L07 키워드 전용 인수
from collections.abc import Callable
import importlib.resources
import json
from typing import Optional

# domain/models.py 에서 데이터 모델 import (R0 표준)
from oss_check.domain.models import Judgement, LicenseInfo

# JSON 등급표 파일 읽기 (DR-04) - 설계지침 v1.2 §4.4 규칙 준수 (importlib.resources 사용)
def load_tiers() -> dict[str, int]:
    try:
        # AGENTS.md 및 설계지침 §4.4: Python 3.11 호환을 위해 / 연산자 사용 (joinpath 인수 다중 전달 금지)
        data_file = importlib.resources.files("oss_check") / "judge" / "tiers.json"
        
        with data_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                k: (v["tier"] if isinstance(v, dict) else v)
                for k, v in data.items()
            }
    except Exception as e:
        # §4.3: 파일이 없거나 읽기 실패 시 빈 표로 넘어가지 않고 예외 발생
        raise FileNotFoundError(f"등급표(tiers.json)를 읽을 수 없습니다: {e}")

TIERS: dict[str, int] = load_tiers()
Rule = Callable[[LicenseInfo, int], Optional[Judgement]]


def rule_proprietary(lic: LicenseInfo, project_tier: int) -> Optional[Judgement]:
    """FR-JDG-09: 독점 라이선스(LicenseRef-*, Proprietary)는 '안 됨'으로 판정"""
    # 설계지침 §4.3 규칙: 독점 판정은 원문(raw)이 아니라 식별자(LicenseRef-*)로 수행
    # 등급표 양식이 SPDX ID 키로 작성되어 식별자 기준 판정 유지
    if lic.options:
        for combo in lic.options:
            for spdx_id in combo:
                if spdx_id.lower().startswith("licenseref-"):
                    return Judgement(
                        lic.package,
                        "안 됨",
                        f"독점 또는 비오픈소스 라이선스({spdx_id})입니다.",
                        spdx_id,
                    )
    return None


def rule_unknown(lic: LicenseInfo, project_tier: int) -> Optional[Judgement]:
    """FR-JDG-07 & FR-JDG-11: 신뢰 수준이 '미상'이거나 표기가 없으면 '모름'으로 판정"""
    if lic.options is None:
        return Judgement(
            lic.package,
            "모름",
            "표기가 없는 코드는 사용 허가가 없는 상태입니다.",
            None,
        )
    return None


class TierRule: #10.09.20:22 규칙 순서를 바꿈
    def __init__(self, tiers: dict[str, int]):
        self._tiers = tiers

    def __call__(self, lic: LicenseInfo, project_tier: int) -> Judgement | None:
        assert lic.options is not None
        best: tuple[int, str] | None = None
        
        for combo in lic.options:                         # OR = 가장 약한 선택지 (FR-JDG-03)
            tiers = [self._tiers.get(x) for x in combo]
            if None in tiers:
                continue
            top = max(zip(tiers, sorted(combo)))          # AND = 가장 센 것 (FR-JDG-04)
            
            if best is None or top[0] < best[0]:
                best = top
                
        if best is None:
            return Judgement(lic.package, "판단보류", "등급표에 없는 라이선스임", None)  # FR-JDG-08
        
        tier, spdx = best
        
        if tier == 2 and project_tier <= 1:              # FR-JDG-05 가 FR-JDG-06 보다 먼저
            return Judgement(lic.package, "조건 있음", f"{spdx}: 고쳐 썼다면 고친 부분만 공개", spdx)
        
        if tier > project_tier:                          # FR-JDG-06
            return Judgement(lic.package, "안 됨", f"{spdx} 조건이 내 프로젝트보다 셈", spdx)
        
        return Judgement(lic.package, "써도 됨", f"{spdx}: 사용 가능", spdx)



# 전략 목록 구성 (우선순위 순서 엄격 적용: FR-JDG-09 -> 07 -> 08 -> 05 -> 06)
RULES: list[Rule] = [rule_proprietary, rule_unknown, TierRule(TIERS)]


# [강의] L07 키워드 전용 인수 - project는 반드시 키워드로 전달받음
def judge(lic: LicenseInfo, *, project: str) -> Judgement:
    """메인 판정 함수"""
    project_tier = TIERS.get(project, 1)  # 내 프로젝트 라이선스 등급 (기본값: MIT 등급 1)
    for rule in RULES:
        if (result := rule(lic, project_tier)) is not None:
            return result
    return Judgement(lic.package, "써도 됨", "사용 가능", None)
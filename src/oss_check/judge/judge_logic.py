# [강의] L05 FCF 디자인 패턴 / L06 사용자 정의 Callable (__call__) / L07 키워드 전용 인수
from collections.abc import Callable
import json
from pathlib import Path
from typing import Optional

from oss_check.domain.models import Judgement, LicenseInfo

# JSON 등급표 파일 읽기 (DR-04)
DATA_PATH = Path(__file__).parent.parent / "data" / "tiers.json"
def load_tiers() -> dict[str, int]:
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # JSON 값이 { "tier": 1, ... } 객체 구조인 경우와 숫자인 경우 모두 대응
            return {
                k: (v["tier"] if isinstance(v, dict) else v)
                for k, v in data.items()
            }
    return {}

TIERS: dict[str, int] = load_tiers()
Rule = Callable[[LicenseInfo, int], Optional[Judgement]]


def rule_proprietary(lic: LicenseInfo, project_tier: int) -> Optional[Judgement]:
    """FR-JDG-09: 독점 라이선스(LicenseRef-*, Proprietary)는 '안 됨'으로 판정"""
    raw_lower = lic.raw.lower()
    if "licenseref-" in raw_lower or "proprietary" in raw_lower:
        return Judgement(lic.package, "안 됨", "독점 또는 비오픈소스 라이선스입니다.", None)
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


class TierRule:
    """FR-JDG-01~06, 08, 12: 등급표 기반 판정 규칙 (Callable 객체)"""

    def __init__(self, tiers: dict[str, int]):
        self._tiers = tiers

    def __call__(self, lic: LicenseInfo, project_tier: int) -> Optional[Judgement]:
        assert lic.options is not None

        # OR/AND 표현식 전개 처리 (FR-JDG-03, FR-JDG-04)
        best: Optional[tuple[int, str]] = None
        for combo in lic.options:  # OR: 가장 약한(낮은 등급) 선택지를 최선으로 채택
            tiers = [self._tiers.get(x) for x in combo]
            if None in tiers:  # 조합 내 등급표에 없는 라이선스가 섞여 있으면 스킵
                continue
            # AND: 조합 내 가장 강한(높은 등급) 라이선스를 기준으로 적용
            top = max(zip(tiers, sorted(combo)))
            if best is None or top[0] < best[0]:
                best = top

        # 등급표에 없는 라이선스인 경우 (FR-JDG-08)
        if best is None:
            return Judgement(
                lic.package, "판단보류", "등급표에 등록되지 않은 라이선스입니다.", None
            )

        tier, spdx = best
        reason_suffix = " (추정된 라이선스 기반)" if lic.confidence == "추정" else ""  # FR-JDG-12

        # FR-JDG-05: 약한 공개조건(LGPL 등 Tier 2) & 내 프로젝트가 허용형(Tier 1 이하)
        if tier == 2 and project_tier <= 1:
            return Judgement(
                lic.package,
                "조건 있음",
                f"{spdx}: 소스 코드를 직접 수정했다면 고친 부분만 공개해야 합니다.{reason_suffix}",
                spdx,
            )

        # FR-JDG-06: 의존성 라이선스 등급이 내 프로젝트 등급보다 높은 경우
        if tier > project_tier:
            return Judgement(
                lic.package,
                "안 됨",
                f"{spdx}: 의존성 라이선스 조건이 내 프로젝트 라이선스보다 엄격합니다.{reason_suffix}",
                spdx,
            )

        # 기본 허용
        return Judgement(lic.package, "써도 됨", f"{spdx}{reason_suffix}", spdx)


# 전략 목록 구성 (우선순위 순서 엄격 적용: FR-JDG-09 -> 07 -> 08 -> 05 -> 06)
RULES: list[Rule] = [rule_proprietary, rule_unknown, TierRule(TIERS)]


# [강의] L07 키워드 전용 인수 - project는 반드시 키워드로 전달받음
def judge(lic: LicenseInfo, *, project: str) -> Judgement:
    """메인 판정 함수"""
    project_tier = TIERS.get(project, 1)  # 내 프로젝트 라이선스 등급 (기본값: MIT 등급 1)
    for rule in RULES:
        if (result := rule(lic, project_tier)) is not None:
            return result
    return Judgement(lic.package, "써도 됨", "", None)
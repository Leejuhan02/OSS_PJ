"""공통 데이터 모델 (R0).

모듈 사이에 주고받는 값의 형식을 여기서 정함. 각 모듈은 이 형식만 믿고 쓰면 됨.

    collect(R1) ──Package──▶ resolve(R2) ──LicenseInfo──▶ judge(R3) ──Judgement──▶ app/web
                                                                   └──▶ Row ─▶ Report

규칙
- 표준 라이브러리 외 import 금지 (설계지침 §2).
- 잘못된 값은 만드는 순간 예외를 냄. 판정 단계에서 뒤늦게 터지지 않게 하려는 것임.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal


# [강의] 열거형(IntEnum): 등급을 숫자처럼 비교하면서 이름으로 읽음 — SRS 부록 A
class Tier(IntEnum):
    PUBLIC_DOMAIN = 0      # 조건 없음 (CC0, Unlicense)
    PERMISSIVE = 1         # 허용형 (MIT, Apache-2.0)
    WEAK_COPYLEFT = 2      # 약한 공개조건 (LGPL, MPL)
    STRONG_COPYLEFT = 3    # 강한 공개조건 (GPL)
    NETWORK_COPYLEFT = 4   # 네트워크 공개조건 (AGPL)


# [강의] 타입 힌트(Literal): 허용 값을 문자열 목록으로 고정
Confidence = Literal["확실", "추정", "미상"]                                 # FR-LIC-08·09
Origin = Literal["license_expression", "license", "classifiers", "none"]  # FR-LIC-01·10
Verdict = Literal["안 됨", "모름", "조건 있음", "판단보류", "써도 됨"]          # FR-JDG-02

CONFIDENCES: tuple[str, ...] = ("확실", "추정", "미상")
ORIGINS: tuple[str, ...] = ("license_expression", "license", "classifiers", "none")
# 위험한 것부터. 이 순서가 화면 정렬 순서임 (FR-OUT-02)
VERDICTS: tuple[str, ...] = ("안 됨", "모름", "조건 있음", "판단보류", "써도 됨")
RISK_ORDER: dict[str, int] = {verdict: rank for rank, verdict in enumerate(VERDICTS)}


# [강의] 데이터클래스(frozen): 만든 뒤 바꿀 수 없는 값 객체
@dataclass(frozen=True)
class Package:
    """의존성 하나. R1이 만듦.

    name    PEP 503 정규화 이름 (소문자, -·_·. 연속은 - 하나) — FR-DEP-04
    version 확정 버전. `이름==버전` 입력에서만 있음 — FR-IN-07
    direct  입력 파일에 직접 적힌 패키지인지 — FR-DEP-07
    depth   직접 = 0, 그 의존성 = 1 … — FR-DEP-07
    lookup_failed  패키지 정보를 가져오지 못했으면 True — FR-DEP-08
                   이 패키지는 라이선스를 식별하지 않고 「모름」으로 판정하되, 사유에 조회 실패를 적음
    """

    name: str
    version: str | None = None
    direct: bool = True
    depth: int = 0
    lookup_failed: bool = False

    def __post_init__(self) -> None:
        if not self.name or self.name != self.name.strip():
            raise ValueError(f"패키지 이름이 비었거나 앞뒤 공백이 있음: {self.name!r}")
        if self.depth < 0:
            raise ValueError(f"depth는 0 이상이어야 함: {self.depth}")
        if self.direct != (self.depth == 0):
            raise ValueError(f"direct와 depth가 맞지 않음: direct={self.direct}, depth={self.depth}")


@dataclass(frozen=True)
class LicenseInfo:
    """패키지 하나의 라이선스 식별 결과. R2가 만들고 R3가 읽음.

    options     SPDX 표현식을 전개한 선택지. OR = 선택지 여러 개, AND = 한 선택지 안의 여러 식별자.
                  "MIT"                   → (frozenset({"MIT"}),)
                  "MIT OR Apache-2.0"     → (frozenset({"MIT"}), frozenset({"Apache-2.0"}))
                  "MPL-2.0 AND MIT"       → (frozenset({"MPL-2.0", "MIT"}),)
                식별 실패(미상)이면 None.
    confidence  확실 / 추정 / 미상. classifier에서 얻었으면 반드시 추정 — FR-LIC-08
    origin      값을 얻은 메타데이터 필드. 미상이면 "none" — FR-LIC-10
    raw         변환 전 원문. 항상 문자열. 원문이 없으면 "".
                  classifier 여러 줄은 "\\n"으로 이어 붙여 넣음.
    """

    package: str
    options: tuple[frozenset[str], ...] | None
    confidence: Confidence
    origin: Origin
    raw: str = ""

    def __post_init__(self) -> None:
        if self.confidence not in CONFIDENCES:
            raise ValueError(f"알 수 없는 신뢰 수준: {self.confidence!r}")
        if self.origin not in ORIGINS:
            raise ValueError(f"알 수 없는 출처: {self.origin!r}")
        if not isinstance(self.raw, str):
            raise TypeError(f"raw는 문자열이어야 함 (튜플·None 금지): {type(self.raw).__name__}")

        unknown = self.options is None
        if unknown != (self.confidence == "미상"):
            raise ValueError("options가 None인 것과 신뢰 수준 「미상」은 항상 함께여야 함")
        if unknown != (self.origin == "none"):
            raise ValueError("options가 None인 것과 출처 \"none\"은 항상 함께여야 함")
        if self.origin == "classifiers" and self.confidence != "추정":
            raise ValueError("classifier에서 얻은 결과는 신뢰 수준이 「추정」이어야 함 (FR-LIC-08)")

        if self.options is not None:
            if not isinstance(self.options, tuple) or not self.options:
                raise ValueError("options는 비어 있지 않은 튜플이어야 함")
            for choice in self.options:
                if not isinstance(choice, frozenset) or not choice:
                    raise ValueError("각 선택지는 비어 있지 않은 frozenset이어야 함")
                if not all(isinstance(identifier, str) and identifier for identifier in choice):
                    raise ValueError("식별자는 비어 있지 않은 문자열이어야 함")

    # [강의] 클래스 메서드: 자주 쓰는 생성 방식에 이름을 붙임
    @classmethod
    def single(cls, package: str, identifier: str, *, confidence: Confidence,
               origin: Origin, raw: str = "") -> LicenseInfo:
        """식별자 하나짜리 결과. 예: LicenseInfo.single("requests", "Apache-2.0", ...)"""
        return cls(package, (frozenset({identifier}),), confidence, origin, raw)

    @classmethod
    def unknown(cls, package: str, raw: str = "") -> LicenseInfo:
        """식별 실패. 원문이 있었다면 raw에 남김 (FR-LIC-10)."""
        return cls(package, None, "미상", "none", raw)

    @property
    def identifiers(self) -> frozenset[str]:
        """모든 선택지에 등장하는 식별자 전체. 미상이면 빈 집합."""
        if self.options is None:
            return frozenset()
        return frozenset().union(*self.options)


@dataclass(frozen=True)
class Judgement:
    """패키지 하나의 판정. R3가 만듦.

    reason            한국어 한 줄 사유. 빈 문자열 금지 — FR-JDG-10
    decisive_license  판정을 결정한 식별자. 미상·독점처럼 특정 식별자가 없으면 None
    """

    package: str
    verdict: Verdict
    reason: str
    decisive_license: str | None = None

    def __post_init__(self) -> None:
        if self.verdict not in VERDICTS:
            raise ValueError(f"알 수 없는 판정: {self.verdict!r}")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("판정에는 사유가 있어야 함 (FR-JDG-10)")


@dataclass(frozen=True)
class Row:
    """결과 화면의 한 줄 = 패키지 + 라이선스 + 판정."""

    package: Package
    license: LicenseInfo
    judgement: Judgement

    def __post_init__(self) -> None:
        names = {self.package.name, self.license.package, self.judgement.package}
        if len(names) != 1:
            raise ValueError(f"한 줄 안의 패키지 이름이 서로 다름: {sorted(names)}")
        if self.package.lookup_failed and self.license.options is not None:
            raise ValueError("조회 실패 패키지에 식별된 라이선스가 있을 수 없음 (FR-DEP-08)")


@dataclass
class Report:
    """분석 결과 전체. app이 만들고 web·CLI가 표시함."""

    project_license: str
    rows: list[Row] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)   # 조회 실패, 건너뛴 줄 — FR-OUT-05

    def sorted_rows(self) -> list[Row]:
        """위험 순, 같은 판정 안에서는 이름 순 — FR-OUT-02"""
        return sorted(self.rows, key=lambda row: (RISK_ORDER[row.judgement.verdict], row.package.name))

    def counts(self) -> dict[str, int]:
        """전체·직접·따라온 패키지 수 — FR-OUT-01. failed = 조회 실패 수 — FR-DEP-08"""
        direct = sum(1 for row in self.rows if row.package.direct)
        failed = sum(1 for row in self.rows if row.package.lookup_failed)
        return {"total": len(self.rows), "direct": direct,
                "transitive": len(self.rows) - direct, "failed": failed}

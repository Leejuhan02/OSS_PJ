"""PyPI info 메타데이터에서 단일 라이선스를 식별한다.

복합 표현식과 여러 라이선스 classifier의 결합은 후속 FR-LIC-05~07 작업이다.
지원하지 않는 값을 부분적으로 읽어 허용형 라이선스로 바꾸지 않는다.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
import json
from pathlib import Path
import re
from typing import Literal


Source = Literal["license_expression", "license", "classifiers"]
Confidence = Literal["확실", "추정", "미상"]


# [강의] 정규표현식: URL과 공백을 정리하되 라이선스 이름을 임의로 추측하지 않는다.
def normalize_license_name(value: str, *, first_line: bool = True) -> str:
    """FR-LIC-03의 이름 정규화. 구조화된 표현식은 전체 문자열을 보존한다."""
    value = value.strip()
    if first_line:
        value = value.splitlines()[0] if value else ""
    value = re.sub(r"https?://[^\s<>\)\]]+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\(\s*\)|\[\s*\]|<\s*>", "", value)
    value = " ".join(value.split()).casefold()
    return re.sub(r"(?:^|\s+)licen[cs]e$", "", value).strip()


# [강의] 데이터클래스: 식별 결과와 근거를 수정 불가능한 값 객체로 묶는다.
@dataclass(frozen=True)
class LicenseEvidence:
    source: Source
    raw: str | tuple[str, ...]


@dataclass(frozen=True)
class LicenseResolution:
    identifier: str | None
    confidence: Confidence
    source: Source | None
    raw: str | tuple[str, ...] | None
    evidence: tuple[LicenseEvidence, ...]


class LicenseResolver:
    """로컬 SPDX 목록과 별칭 사전만 사용한다. data_dir로 데이터 교체 가능."""

    def __init__(self, data_dir: Path | None = None) -> None:
        directory = data_dir if data_dir is not None else files("oss_check").joinpath("data")
        catalog = json.loads(directory.joinpath("spdx_licenses.json").read_text(encoding="utf-8"))
        aliases = json.loads(directory.joinpath("license_aliases.json").read_text(encoding="utf-8"))
        self._identifiers = {
            item["licenseId"].casefold(): item["licenseId"] for item in catalog["licenses"]
        }
        self._names: dict[str, str | None] = {}
        for item in catalog["licenses"]:
            # 옛 GPL-3.0과 현행 -only ID는 이름이 같으므로 이름 검색에는 현행 ID를 쓴다.
            if item.get("isDeprecatedLicenseId", False):
                continue
            name = normalize_license_name(item["name"])
            identifier = item["licenseId"]
            if name in self._names and self._names[name] != identifier:
                self._names[name] = None  # 같은 이름의 다른 라이선스는 추측하지 않는다.
            else:
                self._names[name] = identifier
        self._aliases: dict[str, str] = {}
        for name, target in aliases.items():
            identifier = self._identifiers.get(target.casefold())
            if identifier is None and re.fullmatch(r"LicenseRef-[A-Za-z0-9.-]+", target):
                identifier = target
            if identifier is None:
                raise ValueError(f"별칭의 SPDX 식별자가 유효하지 않습니다: {target}")
            normalized = normalize_license_name(name)
            if normalized in self._aliases and self._aliases[normalized] != identifier:
                raise ValueError(f"서로 다른 라이선스를 가리키는 별칭입니다: {name}")
            if normalized in self._identifiers and self._identifiers[normalized] != identifier:
                raise ValueError(f"SPDX 식별자를 다른 라이선스로 바꾸는 별칭입니다: {name}")
            self._aliases[normalized] = identifier

    def _convert(self, value: str, *, first_line: bool = True) -> str | None:
        normalized = normalize_license_name(value, first_line=first_line)
        if normalized in self._identifiers:
            return self._identifiers[normalized]
        if re.fullmatch(r"licenseref-[a-z0-9.-]+", normalized):
            # 사용자 정의 식별자는 그대로 유지해 R3에서 독점 여부를 판정하게 한다.
            reference = re.search(r"licenseref-([a-z0-9.-]+)", value, flags=re.IGNORECASE)
            return "LicenseRef-" + reference.group(1)
        return self._aliases.get(normalized) or self._names.get(normalized)

    def resolve(self, metadata: Mapping[str, object]) -> LicenseResolution:
        """PyPI 응답의 info 객체를 받는다. 첫 변환 성공 단계에서 반환한다."""
        evidence: list[LicenseEvidence] = []
        # [강의] 반복문·조건문: 필드 존재 여부가 아니라 변환 성공 여부로 다음 단계를 결정한다.
        for source in ("license_expression", "license"):
            raw = metadata.get(source)
            if not isinstance(raw, str) or not raw.strip():
                continue
            evidence.append(LicenseEvidence(source, raw))
            if source == "license" and len(raw) > 200:
                continue
            identifier = self._convert(raw, first_line=source == "license")
            if identifier is not None:
                return LicenseResolution(identifier, "확실", source, raw, tuple(evidence))

        raw_classifiers = metadata.get("classifiers")
        if isinstance(raw_classifiers, (list, tuple)):
            classifiers = tuple(value for value in raw_classifiers if isinstance(value, str))
            if classifiers:
                evidence.append(LicenseEvidence("classifiers", classifiers))
            identifiers: set[str] = set()
            unresolved = False
            for classifier in classifiers:
                parts = [part.strip() for part in classifier.split("::")]
                if len(parts) < 2 or parts[0].casefold() != "license":
                    continue
                # 이 범주 자체는 특정 라이선스가 아니다.
                if len(parts) == 2 and parts[1] == "OSI Approved":
                    continue
                identifier = self._convert(parts[-1], first_line=False)
                if identifier is None:
                    unresolved = True
                else:
                    identifiers.add(identifier)
            # 복수 후보에서 임의로 MIT 등을 고르면 위험하므로 아직은 미상으로 남긴다.
            if len(identifiers) == 1 and not unresolved:
                return LicenseResolution(
                    identifiers.pop(), "추정", "classifiers", classifiers, tuple(evidence)
                )

        return LicenseResolution(None, "미상", None, None, tuple(evidence))


@lru_cache(maxsize=1)
def _default_resolver() -> LicenseResolver:
    """목록은 첫 사용 시 한 번 읽고 프로세스 안에서 재사용한다."""
    return LicenseResolver()


def resolve_license(metadata: Mapping[str, object]) -> LicenseResolution:
    return _default_resolver().resolve(metadata)

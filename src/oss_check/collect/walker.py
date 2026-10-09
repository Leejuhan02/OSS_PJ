"""
src/oss_check/collect/walker.py

요구사항:
- FR-DEP-01: requires_dist 재귀적 전이 의존성 전개
- FR-DEP-02: Python 3.11/Linux x86_64 기준 환경 마커 평가
- FR-DEP-03: extras 요청 시 해당 extras 의존성 포함 및 지연 extras 누적 재전개
- FR-DEP-04: PEP 503 패키지 이름 정규화
- FR-DEP-05: 동일 패키지 중복 fetch 방지 (1회만 조회)
- FR-DEP-06: 순환 의존성 발생 시 정상 종료
- FR-DEP-07: 직접 여부(direct)와 깊이(depth) 기록
- FR-DEP-08: 패키지 정보 조회 실패 시 분석 중단 없이 '조회 실패' 기록
- QR-S-03: 외부 요청 전 PEP 508 이름 규칙 검증
"""
import re
from packaging.requirements import InvalidRequirement, Requirement

# 의존성 전개에 필요한 Package 및 PackageSource 포트를 domain 에서 참조
from oss_check.domain.models import Package
from oss_check.domain.ports import PackageSource

# FR-DEP-02: 환경 마커 평가를 위한 기준 실행 환경 (Python 3.11 / Linux x86_64)
ENV: dict[str, str] = {
    "python_version": "3.11",
    "sys_platform": "linux",
    "platform_system": "Linux",
    "os_name": "posix",
    "platform_machine": "x86_64",
    "implementation_name": "cpython",
    "python_full_version": "3.11.9",
    "platform_python_implementation": "CPython",
}

# QR-S-03: PEP 508 패키지 명명 규칙 검증 정규식
PACKAGE_NAME_PATTERN: re.Pattern = re.compile(
    r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE
)


# [강의] 함수 어노테이션
def normalize(name: str) -> str:
    """
    FR-DEP-04: PEP 503 규칙에 따라 패키지 이름을 정규화 (소문자화 및 [-_.]+ -> -).
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def is_valid_package_name(name: str) -> bool:
    """
    QR-S-03: 외부 URL 호출 전 패키지 이름이 PEP 508 규칙에 맞는지 검증.
    """
    return bool(PACKAGE_NAME_PATTERN.match(name))


def _should_include_dep(req: Requirement, parent_extras: frozenset[str]) -> bool:
    """
    FR-DEP-02, FR-DEP-03: 기준 환경 및 부모 extras 기준 마커 평가.
    """
    if not req.marker:
        return True
    envs = [dict(ENV, extra=e) for e in parent_extras] or [dict(ENV, extra="")]
    return any(req.marker.evaluate(env) for env in envs)


def walk(
    roots: list[str | object],
    source: PackageSource,
    warnings: list[str] | None = None,
) -> list[Package]:
    """
    FR-DEP-01 ~ 08: roots 목록에서 시작하여 전이 의존성을 재귀적으로 전개.
    - roots: 요구사항 문자열 리스트 또는 ParsedRequirement 리스트
    - source: 메타데이터 조회를 위한 PackageSource 포트 구현체
    - warnings: 조회 실패 등의 경고 메시지를 담을 리스트 (선택적)
    """
    seen: dict[str, Package] = {}
    evaluated_extras: dict[str, set[str]] = {}
    cached_info: dict[str, dict | None] = {}

    # 큐 항목: (raw_string, depth, parent_extras, is_direct, pinned_version)
    queue: list[tuple[str, int, frozenset[str], bool, str | None]] = []

    for r in roots:
        raw_str = getattr(r, "raw", str(r))
        pinned = getattr(r, "pinned_version", None)
        extras = getattr(r, "extras", frozenset())
        queue.append((raw_str, 0, frozenset(extras), True, pinned))

    while queue:
        raw, depth, parent_extras, is_direct, pinned_version = queue.pop(0)

        try:
            req = Requirement(raw)
        except InvalidRequirement:
            continue

        if not _should_include_dep(req, parent_extras):
            continue

        norm_name = normalize(req.name)
        if not is_valid_package_name(norm_name):
            if warnings is not None:
                warnings.append(f"유효하지 않은 패키지 이름입니다: '{norm_name}'")
            continue

        current_extras = set(req.extras)

        if norm_name not in seen:
            seen[norm_name] = Package(
                name=norm_name,
                version=pinned_version,
                direct=is_direct,
                depth=depth,
            )

            # FR-DEP-05: 동일 패키지는 1회만 조회
            if norm_name not in cached_info:
                cached_info[norm_name] = source.fetch(norm_name)
            info = cached_info[norm_name]

            # FR-DEP-08: 패키지 정보 조회 실패 시 중단 없이 표시 및 경고 기록
            if info is None:
                if warnings is not None:
                    warnings.append(f"패키지 '{norm_name}'의 정보를 가져오지 못했습니다 (조회 실패).")
                evaluated_extras[norm_name] = set(current_extras)
                continue

            evaluated_extras[norm_name] = set(current_extras)
            for dep in (info or {}).get("requires_dist") or []:
                queue.append((dep, depth + 1, frozenset(current_extras), False, None))

        else:
            # 직접 의존성 승격 (전이로 먼저 만났으나 이후 루트에 있는 경우)
            if is_direct and not seen[norm_name].direct:
                seen[norm_name] = Package(
                    name=norm_name,
                    version=pinned_version or seen[norm_name].version,
                    direct=True,
                    depth=0,
                )

            # FR-DEP-03: 새 extras 유입 시 재전개 (FR-DEP-05/06: 중복/순환 시 스킵)
            already_evaluated = evaluated_extras.get(norm_name, set())
            new_extras = current_extras - already_evaluated
            if not new_extras:
                continue

            already_evaluated.update(new_extras)
            info = cached_info.get(norm_name)
            if info is None:
                continue

            for dep in (info or {}).get("requires_dist") or []:
                queue.append((dep, depth + 1, frozenset(new_extras), False, None))

    return list(seen.values())


def walk_with_warnings(
    roots: list[str | object],
    source: PackageSource,
) -> tuple[list[Package], list[str]]:
    """
    walk 실행 결과와 함께 수집된 경고 목록(조회 실패 등)을 반환하는 편의 함수.
    """
    warnings: list[str] = []
    packages = walk(roots, source, warnings=warnings)
    return packages, warnings

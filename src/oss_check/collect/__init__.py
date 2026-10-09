"""
src/oss_check/collect/__init__.py

R1 수집 모듈:
- FR-IN: 입력 파싱 (requirements.txt, 주석 무시, PEP 508 파싱, 크기 제한 등)
- FR-DEP: 전이 의존성 재귀 전개, 마커 평가, extras 처리, PEP 503 정규화 등
"""
from oss_check.collect.parser import (
    DEFAULT_PROJECT_LICENSE,
    MAX_INPUT_SIZE,
    ParsedRequirement,
    check_input_size,
    extract_pinned_version,
    get_project_license,
    parse_requirements,
)
try:
    from oss_check.collect.walker import (
        ENV,
        is_valid_package_name,
        normalize,
        walk,
        walk_with_warnings,
    )
except ImportError:  # R0의 domain/models.py 또는 ports.py가 아직 제공되지 않은 경우
    pass

__all__ = [
    "DEFAULT_PROJECT_LICENSE",
    "MAX_INPUT_SIZE",
    "ParsedRequirement",
    "check_input_size",
    "extract_pinned_version",
    "get_project_license",
    "parse_requirements",
    "ENV",
    "is_valid_package_name",
    "normalize",
    "walk",
    "walk_with_warnings",
]

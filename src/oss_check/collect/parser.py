"""
src/oss_check/collect/parser.py

요구사항:
- FR-IN-01: requirements.txt 파일 내용 입력 처리
- FR-IN-02: 텍스트 붙여넣기 입력 처리 (파일 입력과 동일)
- FR-IN-03: 주석(#) 및 빈 줄 무시
- FR-IN-04: PEP 508 표기(이름, extras, 버전 지정, 환경 마커) 파싱
- FR-IN-05: 해석 불가 줄(-r, -e, URL 등) 건너뛰기 및 줄 번호/사유 경고 기록
- FR-IN-06: 프로젝트 라이선스 기본값 MIT 처리
- FR-IN-07: 이름==버전 형식의 확정 버전(pinned version) 추출
- FR-IN-08: 1MB 초과 입력 제한
"""
from dataclasses import dataclass
import re
from packaging.requirements import InvalidRequirement, Requirement

# FR-IN-08: 입력 크기 제한 (1MB = 1,048,576 bytes)
MAX_INPUT_SIZE: int = 1_048_576

# FR-IN-06: 기본 프로젝트 라이선스
DEFAULT_PROJECT_LICENSE: str = "MIT"

# FR-IN-05: 지원하지 않는 pip 옵션 및 URL 패턴 접두사
UNSUPPORTED_PREFIXES: tuple[str, ...] = (
    "-r", "--requirement",
    "-e", "--editable",
    "-f", "--find-links",
    "-i", "--index-url",
    "--extra-index-url",
    "--no-index",
    "-c", "--constraint",
    "--pre",
)
URL_SCHEME_PATTERN: re.compile = re.compile(r"^[a-zA-Z][a-zA-Z0-9+-.]*://")


@dataclass(frozen=True)
class ParsedRequirement:
    """파싱된 단일 요구사항 항목"""
    raw: str
    name: str
    pinned_version: str | None
    extras: frozenset[str]
    marker: str | None
    line_number: int


def get_project_license(license_name: str | None) -> str:
    """
    FR-IN-06: 사용자가 프로젝트 라이선스를 고르지 않으면 MIT를 기준으로 반환.
    """
    if not license_name or not license_name.strip():
        return DEFAULT_PROJECT_LICENSE
    return license_name.strip()


def check_input_size(content: str | bytes) -> None:
    """
    FR-IN-08: 입력 크기가 1MB를 초과하면 ValueError 발생.
    """
    size = len(content) if isinstance(content, bytes) else len(content.encode("utf-8"))
    if size > MAX_INPUT_SIZE:
        raise ValueError(
            f"입력 크기({size:,} bytes)가 허용 한도인 1MB({MAX_INPUT_SIZE:,} bytes)를 초과했습니다."
        )


def extract_pinned_version(req: Requirement) -> str | None:
    """
    FR-IN-07: '이름==버전' 형식인 경우 확정 버전을 추출.
    단일 '==' 연산자이며 와일드카드('*')가 아닌 경우에만 확정 버전으로 인정.
    """
    specs = list(req.specifier)
    if len(specs) == 1 and specs[0].operator == "==" and not specs[0].version.endswith(".*"):
        return specs[0].version
    return None


def _is_unsupported_line(line: str) -> str | None:
    """
    FR-IN-05: 지원하지 않는 옵션이나 URL 구문인지 판별하고 사유를 반환.
    """
    for prefix in UNSUPPORTED_PREFIXES:
        if line.startswith(prefix):
            return f"지원하지 않는 옵션('{prefix}')입니다."
    if URL_SCHEME_PATTERN.match(line) or "://" in line or line.startswith("git+"):
        return "URL/VCS 형식의 직접 참조는 지원하지 않습니다."
    if line.startswith("-"):
        return f"지원하지 않는 옵션 플래그('{line.split()[0]}')입니다."
    return None


def parse_requirements(content: str | bytes) -> tuple[list[ParsedRequirement], list[str]]:
    """
    FR-IN-01 ~ FR-IN-08: requirements 텍스트나 파일 내용을 파싱하여
    유효한 요구사항 목록과 건너뛴 줄 경고 목록을 반환.
    """
    # 1. 크기 검사 (FR-IN-08)
    check_input_size(content)

    text = content.decode("utf-8") if isinstance(content, bytes) else content
    lines = text.splitlines()

    parsed_list: list[ParsedRequirement] = []
    warnings: list[str] = []

    for lineno, raw_line in enumerate(lines, start=1):
        # 2. 주석(#) 및 빈 줄 무시 (FR-IN-03)
        # 인라인 주석 제거: foo==1.0 # 주석 -> foo==1.0
        cleaned = raw_line.partition("#")[0].strip()
        if not cleaned:
            continue

        # 3. 지원하지 않는 옵션/URL 검사 (FR-IN-05)
        unsupported_reason = _is_unsupported_line(cleaned)
        if unsupported_reason:
            warnings.append(f"Line {lineno}: '{cleaned}' - {unsupported_reason}")
            continue

        # 4. PEP 508 파싱 (FR-IN-04)
        try:
            req = Requirement(cleaned)
        except InvalidRequirement as e:
            warnings.append(f"Line {lineno}: '{cleaned}' - PEP 508 파싱 실패: {e}")
            continue

        # 5. 확정 버전 추출 (FR-IN-07)
        pinned = extract_pinned_version(req)
        marker_str = str(req.marker) if req.marker else None

        parsed_list.append(
            ParsedRequirement(
                raw=cleaned,
                name=req.name,
                pinned_version=pinned,
                extras=frozenset(req.extras),
                marker=marker_str,
                line_number=lineno,
            )
        )

    return parsed_list, warnings

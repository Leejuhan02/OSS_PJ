"""R2 공개 API: 내부 식별 결과를 공통 LicenseInfo로 변환한다 (§4)."""

from oss_check.domain.models import LicenseInfo

from .metadata import resolve_license


def _raw_text(raw: str | tuple[str, ...] | None) -> str:
    """classifier 여러 줄도 공통 모델에는 문자열 하나로 전달한다."""
    if isinstance(raw, tuple):
        return "\n".join(raw)
    return raw or ""


# [강의] 클린 아키텍처: R2 내부 결과를 공통 모델로 바꿔 R0·R3에 전달한다.
def identify(name: str, info: dict) -> LicenseInfo:
    """FR-LIC-01: 첫 변환 성공 결과를 공통 LicenseInfo로 반환한다.

    미상일 때는 확인한 첫 필드의 원문을 남기고, 원문이 없으면 빈 문자열을 쓴다.
    패키지 이름은 수집 단계에서 받은 값을 그대로 유지한다.
    """
    result = resolve_license(info)
    if result.options is None:
        raw = result.evidence[0].raw if result.evidence else None
        return LicenseInfo.unknown(name, raw=_raw_text(raw))

    assert result.source is not None
    return LicenseInfo(
        name, result.options, confidence=result.confidence,
        origin=result.source, raw=_raw_text(result.raw),
    )

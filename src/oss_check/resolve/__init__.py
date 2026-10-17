"""R2 공개 계약: identify(name, info) → LicenseInfo."""

from .api import identify
# 기존 R2 단위 테스트를 위한 호환 이름. 다른 모듈은 identify만 사용한다.
from .metadata import LicenseResolver, resolve_license

__all__ = ["identify"]

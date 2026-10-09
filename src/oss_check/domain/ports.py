"""외부 데이터 조회 규격(포트) (R0).

수집·식별·취약점 모듈은 PyPI나 OSV를 직접 부르지 않고 이 규격만 씀.
실제 구현(어댑터)은 adapters/ 에 둠 (R4). 테스트에서는 같은 규격의 가짜 구현을 꽂아
네트워크 없이 실행함 — DC-05.

    collect.walker ──fetch(name)──▶ PackageSource ◀── adapters.PyPIPackageSource  (실제)
                                                  ◀── 테스트의 FakePackageSource  (가짜)

규칙
- 표준 라이브러리 외 import 금지 (설계지침 §2).
- 구현체는 네트워크 오류·시간 초과를 예외로 올리지 않고 None(또는 빈 결과)으로 돌려줌.
  분석 전체가 멈추지 않게 하려는 것임 — FR-DEP-08, FR-VUL-05.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from oss_check.domain.models import Package


# [강의] 추상 기반 클래스(ABC): 구현해야 할 메서드를 강제함
class PackageSource(ABC):
    """패키지 메타데이터 조회 규격. 실제 구현은 PyPI JSON API — IF-SW-01."""

    @abstractmethod
    def fetch(self, name: str) -> dict[str, Any] | None:
        """패키지 하나의 메타데이터를 돌려줌.

        name    PEP 503 정규화된 이름. 호출 전에 이름 형식 검증을 마친 값 — QR-S-03
        반환    PyPI JSON 응답의 "info" 객체 (dict). 최소한 아래 키를 씀.
                  requires_dist       의존성 목록 (없으면 None 또는 [])  ← R1
                  license_expression  SPDX 표현식                          ← R2
                  license             옛 라이선스 필드                      ← R2
                  classifiers         분류자 목록                          ← R2
                패키지가 없거나(404) 조회에 실패하면 None — FR-DEP-08
        """


class VulnSource(ABC):
    """알려진 취약점 조회 규격. 실제 구현은 OSV — IF-SW-03·04. 권장(S) 범위."""

    @abstractmethod
    def query(self, packages: Sequence[Package]) -> dict[str, list[dict[str, Any]]]:
        """여러 패키지의 취약점을 한 번에 조회함.

        packages  조회할 패키지들. 확정 버전(version)이 없는 패키지는 조회하지 않음 — FR-VUL-02
        반환      {패키지 이름: [OSV 권고 dict, ...]}. 취약점이 없는 패키지는 키를 빼거나 빈 목록.
                  조회 자체가 실패하면 빈 dict — FR-VUL-05
        """

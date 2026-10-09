"""
tests/test_FR_DEP_walker.py

FR-DEP 요구사항 단위 테스트:
- FR-DEP-01: 전이 의존성 재귀 전개
- FR-DEP-02: 기준 환경(Python 3.11/Linux) 마커 평가
- FR-DEP-03: extras 요청 시 의존성 포함 및 새 extras 유입 시 재전개
- FR-DEP-04: PEP 503 패키지 이름 정규화
- FR-DEP-05: 동일 패키지 1회만 조회 (중복 조회 방지)
- FR-DEP-06: 순환 의존성 발생 시 정상 종료
- FR-DEP-07: 직접 여부 및 깊이 기록
- FR-DEP-08: 패키지 정보 조회 실패 시 중단 없이 표시 및 경고
- QR-S-03: PEP 508 이름 유효성 검증
"""
import unittest

from oss_check.domain.ports import PackageSource
from oss_check.collect.walker import (
    ENV,
    is_valid_package_name,
    normalize,
    walk,
    walk_with_warnings,
)


class FakePackageSource(PackageSource):
    """설계지침 §5.4에 따른 외부 네트워크 독립 테스트용 가짜 PackageSource 구현체"""
    def __init__(self, data: dict[str, dict | None]):
        self._data = data
        self.call_count: dict[str, int] = {}

    def fetch(self, name: str) -> dict | None:
        self.call_count[name] = self.call_count.get(name, 0) + 1
        return self._data.get(name)


class TestFRDEPWalker(unittest.TestCase):
    def test_FR_DEP_04_normalize_pep503(self):
        """FR-DEP-04: PEP 503 정규화 규칙 (소문자, [-_.]+를 단일 -로 변환) 검증."""
        self.assertEqual(normalize("Flask-CORS"), "flask-cors")
        self.assertEqual(normalize("flask_cors"), "flask-cors")
        self.assertEqual(normalize("flask.cors"), "flask-cors")
        self.assertEqual(normalize("Flask--__..cors"), "flask-cors")

    def test_QR_S_03_is_valid_package_name(self):
        """QR-S-03: PEP 508 패키지 명명 규칙 검증."""
        self.assertTrue(is_valid_package_name("requests"))
        self.assertTrue(is_valid_package_name("foo-bar_1.0"))
        self.assertFalse(is_valid_package_name("-foo"))
        self.assertFalse(is_valid_package_name("foo-"))
        self.assertFalse(is_valid_package_name("foo@bar"))
        self.assertFalse(is_valid_package_name("foo bar"))

    def test_FR_DEP_01_and_07_recursive_transitive_walk(self):
        """FR-DEP-01, FR-DEP-07: 전이 의존성 재귀 전개 및 direct, depth 기록 검증."""
        data = {
            "pkg-a": {"requires_dist": ["pkg-b>=1.0", "pkg-c"]},
            "pkg-b": {"requires_dist": ["pkg-d"]},
            "pkg-c": {"requires_dist": []},
            "pkg-d": {"requires_dist": []},
        }
        source = FakePackageSource(data)
        packages = walk(["pkg-a==1.0.0"], source)

        pkg_map = {p.name: p for p in packages}
        self.assertEqual(len(packages), 4)

        # pkg-a: direct=True, depth=0
        self.assertTrue(pkg_map["pkg-a"].direct)
        self.assertEqual(pkg_map["pkg-a"].depth, 0)

        # pkg-b, pkg-c: direct=False, depth=1
        self.assertFalse(pkg_map["pkg-b"].direct)
        self.assertEqual(pkg_map["pkg-b"].depth, 1)
        self.assertFalse(pkg_map["pkg-c"].direct)
        self.assertEqual(pkg_map["pkg-c"].depth, 1)

        # pkg-d: direct=False, depth=2
        self.assertFalse(pkg_map["pkg-d"].direct)
        self.assertEqual(pkg_map["pkg-d"].depth, 2)

    def test_FR_DEP_02_environment_marker_filtering(self):
        """FR-DEP-02: 기준 환경(Python 3.11, Linux x86_64) 마커 평가 및 불일치 제외."""
        data = {
            "root": {
                "requires_dist": [
                    "dep-linux; sys_platform == 'linux'",
                    "dep-win; sys_platform == 'win32'",
                    "dep-py311; python_version == '3.11'",
                    "dep-py38; python_version < '3.8'",
                ]
            },
            "dep-linux": {"requires_dist": []},
            "dep-win": {"requires_dist": []},
            "dep-py311": {"requires_dist": []},
            "dep-py38": {"requires_dist": []},
        }
        source = FakePackageSource(data)
        packages = walk(["root"], source)

        names = {p.name for p in packages}
        self.assertIn("root", names)
        self.assertIn("dep-linux", names)
        self.assertIn("dep-py311", names)
        self.assertNotIn("dep-win", names)
        self.assertNotIn("dep-py38", names)

    def test_FR_DEP_03_extras_inclusion_and_reexpansion(self):
        """
        FR-DEP-03: extras 요청 시 해당 의존성 포함 및
        초기에 extras 없이 전개된 패키지에 새로운 extras가 유입될 때 재전개 검증.
        (설계지침 §5.6 주의사항: jsonschema[format] -> rfc3987 유입)
        """
        data = {
            "pkg-main": {"requires_dist": ["jsonschema"]},
            "pkg-format-plugin": {"requires_dist": ["jsonschema[format]"]},
            "jsonschema": {
                "requires_dist": [
                    "attrs>=22.2.0",
                    "rfc3987; extra == 'format'",
                ]
            },
            "attrs": {"requires_dist": []},
            "rfc3987": {"requires_dist": []},
        }
        source = FakePackageSource(data)

        # pkg-main(jsonschema 무옵션)과 pkg-format-plugin(jsonschema[format]) 동시 입력
        packages = walk(["pkg-main", "pkg-format-plugin"], source)
        names = {p.name for p in packages}

        self.assertIn("jsonschema", names)
        self.assertIn("attrs", names)
        self.assertIn("rfc3987", names)  # format extra에 의해 포함되어야 함

    def test_FR_DEP_05_and_06_deduplication_and_circular_dependency(self):
        """
        FR-DEP-05: 같은 패키지는 1번만 fetch
        FR-DEP-06: 순환 의존성(A -> B -> A) 발생 시 무한 루프 없이 정상 종료
        """
        data = {
            "pkg-a": {"requires_dist": ["pkg-b"]},
            "pkg-b": {"requires_dist": ["pkg-a", "pkg-c"]},
            "pkg-c": {"requires_dist": ["pkg-a"]},
        }
        source = FakePackageSource(data)
        packages = walk(["pkg-a"], source)

        names = {p.name for p in packages}
        self.assertEqual(names, {"pkg-a", "pkg-b", "pkg-c"})

        # 모든 패키지가 정확히 1번만 fetch 되었는지 확인 (FR-DEP-05)
        self.assertEqual(source.call_count["pkg-a"], 1)
        self.assertEqual(source.call_count["pkg-b"], 1)
        self.assertEqual(source.call_count["pkg-c"], 1)

    def test_FR_DEP_08_fetch_failure_handling(self):
        """
        FR-DEP-08: 패키지 정보 조회 실패(None) 시 분석을 멈추지 않고 패키지 및 경고 기록.
        """
        data = {
            "root": {"requires_dist": ["not-found-pkg", "valid-pkg"]},
            "valid-pkg": {"requires_dist": []},
            # "not-found-pkg"는 딕셔너리에 없으므로 fetch가 None 반환
        }
        source = FakePackageSource(data)
        packages, warnings = walk_with_warnings(["root"], source)

        pkg_map = {p.name: p for p in packages}
        self.assertIn("root", pkg_map)
        self.assertIn("valid-pkg", pkg_map)
        self.assertIn("not-found-pkg", pkg_map)

        # 조회 실패 경고가 warnings에 남아 있어야 함
        self.assertTrue(any("not-found-pkg" in w and "조회 실패" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()

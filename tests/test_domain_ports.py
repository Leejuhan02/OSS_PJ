"""외부 조회 규격(domain/ports.py) 테스트. 네트워크 없이 실행됨."""

import unittest

from oss_check.domain.models import Package
from oss_check.domain.ports import PackageSource, VulnSource


class FakePackageSource(PackageSource):
    def __init__(self, data):
        self._data = data

    def fetch(self, name):
        return self._data.get(name)


class FakeVulnSource(VulnSource):
    def query(self, packages):
        return {p.name: [{"id": "GHSA-test"}] for p in packages if p.version is not None}


class PortTests(unittest.TestCase):
    def test_ports_cannot_be_used_without_implementation(self):
        for port in (PackageSource, VulnSource):
            with self.subTest(port=port.__name__), self.assertRaises(TypeError):
                port()

    def test_incomplete_implementation_is_rejected(self):
        class Broken(PackageSource):
            pass
        with self.assertRaises(TypeError):
            Broken()

    def test_fake_package_source_follows_contract(self):
        source = FakePackageSource({"requests": {"requires_dist": ["idna"], "license_expression": "Apache-2.0"}})
        self.assertEqual(source.fetch("requests")["requires_dist"], ["idna"])
        self.assertIsNone(source.fetch("ghost"))   # 조회 실패는 예외가 아니라 None

    def test_fake_vuln_source_skips_unpinned(self):
        result = FakeVulnSource().query([Package("a", "1.0"), Package("b")])
        self.assertEqual(list(result), ["a"])


if __name__ == "__main__":
    unittest.main()

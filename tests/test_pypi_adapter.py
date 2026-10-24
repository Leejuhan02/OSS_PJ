import unittest
from pypi_adapter import PyPIPackageSource

class TestPyPIPackageSource(unittest.TestCase):
    def test_fetch_info_extract(self):
        adapter = PyPIPackageSource()
        result = adapter.fetch("requests")
        
        self.assertIn("name", result)
        self.assertEqual(result["name"].lower(), "requests")

if __name__ == '__main__':
    unittest.main()
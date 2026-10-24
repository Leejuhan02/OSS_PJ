import unittest
from pypi_adapter import PyPIAdapter

class TestPyPIAdapter(unittest.TestCase):
    def test_fetch_info_extract(self):
        adapter = PyPIAdapter()
        result = adapter.fetch("requests")
        
        self.assertIn("name", result)
        self.assertEqual(result["name"].lower(), "requests")

if __name__ == '__main__':
    unittest.main()
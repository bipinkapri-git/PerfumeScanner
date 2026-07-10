import unittest
from perfume_scanner.main import scan_perfume


class TestPerfumeScanner(unittest.TestCase):
    """Test suite for Perfume Scanner."""

    def test_scan_perfume(self):
        """Test that the scanner returns the expected active status message."""
        result = scan_perfume()
        self.assertIn("active and ready", result)


if __name__ == "__main__":
    unittest.main()

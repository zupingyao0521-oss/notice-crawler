import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from main import notice_date_key


class NoticeDateKeyTests(unittest.TestCase):
    def test_supports_common_chinese_date_format(self):
        self.assertEqual(
            notice_date_key({"date": "2026年7月6日"}),
            (2026, 7, 6),
        )

    def test_missing_date_sorts_last(self):
        self.assertEqual(notice_date_key({"date": ""}), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()

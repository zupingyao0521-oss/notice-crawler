import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from notice_crawler.state import ProcessedArticleStore


class ProcessedArticleStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_stores_article_metadata_without_duplicates(self):
        store = ProcessedArticleStore(self.root / "state.db")
        article = {
            "link": "https://example.com/notice",
            "title": "选课通知",
            "site_name": "教务处",
            "date": "2026-07-06",
        }

        self.assertEqual(store.add_articles([article]), 1)
        self.assertEqual(store.add_articles([article]), 0)
        self.assertTrue(store.contains(article["link"]))
        self.assertEqual(store.load_links(), {article["link"]})
        self.assertEqual(store.count(), 1)

    def test_migrates_legacy_json_idempotently(self):
        legacy_path = self.root / "processed_links.json"
        legacy_path.write_text(
            json.dumps(["https://example.com/a", "https://example.com/b"]),
            encoding="utf-8",
        )
        database_path = self.root / "state.db"

        first_store = ProcessedArticleStore(database_path, legacy_path)
        second_store = ProcessedArticleStore(database_path, legacy_path)

        self.assertEqual(first_store.count(), 2)
        self.assertEqual(second_store.count(), 2)


if __name__ == "__main__":
    unittest.main()

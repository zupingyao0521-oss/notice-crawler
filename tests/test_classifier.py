import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from notice_crawler.classifier import classify_article, sort_articles_by_importance


class ClassifierTests(unittest.TestCase):
    def test_assigns_multiple_tags_and_urgent_importance(self):
        article = classify_article({
            "title": "补考报名紧急通知",
            "summary": "今日截止，请务必完成报名。",
            "key_points": [],
        })

        self.assertEqual(article["importance"], "紧急")
        self.assertEqual(article["importance_score"], 3)
        self.assertIn("考试", article["tags"])
        self.assertIn("报名", article["tags"])

    def test_uses_other_and_normal_as_defaults(self):
        article = classify_article({"title": "校园新闻"})

        self.assertEqual(article["tags"], ["其他"])
        self.assertEqual(article["importance"], "一般")

    def test_sorts_by_importance_then_date(self):
        articles = [
            {"title": "A", "importance_score": 1, "date": "2026-07-06"},
            {"title": "B", "importance_score": 3, "date": "2026-07-01"},
            {"title": "C", "importance_score": 3, "date": "2026年7月5日"},
        ]

        result = sort_articles_by_importance(articles)

        self.assertEqual([article["title"] for article in result], ["C", "B", "A"])


if __name__ == "__main__":
    unittest.main()

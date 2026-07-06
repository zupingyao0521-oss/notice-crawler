import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from notice_crawler.mailer import build_alert_bodies, build_articles_html


class BuildArticlesHtmlTests(unittest.TestCase):
    def test_renders_digest_content(self):
        result = build_articles_html([
            {
                "title": "选课通知",
                "link": "https://example.com/notice",
                "date": "2026-07-06",
                "summary": "请按时完成选课。",
                "key_points": ["截止时间：7月10日", "登录教务系统办理"],
            }
        ])

        self.assertIn("本次共发现 <strong", result)
        self.assertIn("选课通知", result)
        self.assertIn("截止时间：7月10日", result)
        self.assertIn('href="https://example.com/notice"', result)
        self.assertIn('role="presentation"', result)

    def test_escapes_untrusted_article_content(self):
        result = build_articles_html([
            {
                "title": "<script>alert(1)</script>",
                "link": 'https://example.com/?a=1&b="unsafe"',
                "summary": "A & B",
                "key_points": ["<b>not markup</b>"],
            }
        ])

        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)
        self.assertIn("A &amp; B", result)
        self.assertIn("&lt;b&gt;not markup&lt;/b&gt;", result)
        self.assertIn("&amp;b=&quot;unsafe&quot;", result)


class BuildAlertBodiesTests(unittest.TestCase):
    def test_contains_failure_details_and_beijing_time(self):
        text_body, html_body = build_alert_bodies(
            failures=[{
                "kind": "文章正文",
                "name": "测试通知",
                "url": "https://example.com/notice",
                "error": "连接超时",
                "attempts": 3,
            }],
            success_count=2,
            environment="GitHub Actions",
            now=datetime(
                2026,
                7,
                6,
                8,
                0,
                tzinfo=timezone(timedelta(hours=8), name="CST"),
            ),
        )

        for content in (text_body, html_body):
            self.assertIn("测试通知", content)
            self.assertIn("连接超时", content)
            self.assertIn("2026-07-06 08:00:00 CST", content)
            self.assertIn("GitHub Actions", content)
        self.assertIn("成功数量：2", text_body)
        self.assertIn("失败数量：1", text_body)


if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from notice_crawler.summarizer import summarize_article_with_local_llm


class OllamaSummarizerTests(unittest.TestCase):
    @patch("notice_crawler.summarizer.requests.post")
    def test_cloud_request_uses_bearer_auth_without_schema(self, post):
        response = Mock()
        response.json.return_value = {
            "message": {
                "content": '```json\n{"summary":"摘要","key_points":["要点"]}\n```'
            }
        }
        post.return_value = response

        with patch.dict(os.environ, {"OLLAMA_API_KEY": "secret-value"}):
            result = summarize_article_with_local_llm(
                title="测试通知",
                body="正文",
                model="qwen3.5:397b",
                ollama_base_url="https://ollama.com",
                api_key_env="OLLAMA_API_KEY",
            )

        self.assertEqual(result["summary"], "摘要")
        call = post.call_args
        self.assertEqual(call.kwargs["headers"]["Authorization"], "Bearer secret-value")
        self.assertNotIn("format", call.kwargs["json"])
        self.assertEqual(call.args[0], "https://ollama.com/api/chat")

    @patch("notice_crawler.summarizer.requests.post")
    def test_local_request_keeps_structured_output_schema(self, post):
        response = Mock()
        response.json.return_value = {
            "message": {"content": '{"summary":"摘要","key_points":[]}'},
        }
        post.return_value = response

        summarize_article_with_local_llm("标题", "正文")

        call = post.call_args
        self.assertIn("format", call.kwargs["json"])
        self.assertEqual(call.kwargs["headers"], {})

    def test_cloud_request_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OLLAMA_API_KEY"):
                summarize_article_with_local_llm(
                    "标题",
                    "正文",
                    ollama_base_url="https://ollama.com",
                    api_key_env="OLLAMA_API_KEY",
                )


if __name__ == "__main__":
    unittest.main()

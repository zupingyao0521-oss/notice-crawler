import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from notice_crawler.crawler import FetchError, request_with_retry


def response_with_status(status_code):
    response = requests.Response()
    response.status_code = status_code
    response.url = "https://example.com"
    return response


class RequestWithRetryTests(unittest.TestCase):
    def test_retries_connection_error_then_succeeds(self):
        success = response_with_status(200)
        request_get = Mock(side_effect=[requests.ConnectionError("offline"), success])
        sleep = Mock()

        result = request_with_retry(
            "https://example.com",
            max_attempts=3,
            backoff_seconds=[2, 4, 8],
            request_get=request_get,
            sleep=sleep,
        )

        self.assertIs(result, success)
        self.assertEqual(request_get.call_count, 2)
        sleep.assert_called_once_with(2.0)

    def test_raises_after_all_server_errors(self):
        request_get = Mock(side_effect=[
            response_with_status(500),
            response_with_status(502),
            response_with_status(503),
        ])
        sleep = Mock()

        with self.assertRaises(FetchError) as caught:
            request_with_retry(
                "https://example.com",
                max_attempts=3,
                backoff_seconds=[2, 4, 8],
                request_get=request_get,
                sleep=sleep,
            )

        self.assertEqual(caught.exception.attempts, 3)
        self.assertEqual(request_get.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2.0, 4.0])

    def test_does_not_retry_404(self):
        request_get = Mock(return_value=response_with_status(404))
        sleep = Mock()

        with self.assertRaises(FetchError) as caught:
            request_with_retry(
                "https://example.com/missing",
                request_get=request_get,
                sleep=sleep,
            )

        self.assertEqual(caught.exception.attempts, 1)
        self.assertEqual(request_get.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()

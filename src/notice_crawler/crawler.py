from urllib.parse import urljoin
import re
import time

import requests
from bs4 import BeautifulSoup


class FetchError(RuntimeError):
    def __init__(self, url, attempts, last_error):
        self.url = url
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"请求失败（尝试 {attempts} 次）：{last_error}")


def request_with_retry(
    url,
    max_attempts=3,
    backoff_seconds=(2, 4, 8),
    timeout=10,
    request_get=requests.get,
    sleep=time.sleep,
):
    max_attempts = max(1, int(max_attempts))
    delays = [max(0, float(value)) for value in backoff_seconds]

    for attempt in range(1, max_attempts + 1):
        last_error = None
        try:
            response = request_get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=timeout,
            )
            response.raise_for_status()
            return response
        except requests.HTTPError as error:
            last_error = error
            status_code = error.response.status_code if error.response is not None else None
            should_retry = status_code is not None and status_code >= 500
        except (requests.ConnectionError, requests.Timeout) as error:
            last_error = error
            should_retry = True
        except requests.RequestException as error:
            last_error = error
            should_retry = False

        if not should_retry or attempt == max_attempts:
            raise FetchError(url, attempt, last_error) from last_error

        delay = delays[min(attempt - 1, len(delays) - 1)] if delays else 0
        print(f"请求失败，{delay:g} 秒后进行第 {attempt + 1} 次尝试：{url} - {last_error}")
        sleep(delay)


def get_school_notices(
    url,
    item_selector,
    title_selector="a",
    date_selector=None,
    max_attempts=3,
    backoff_seconds=(2, 4, 8),
):
    response = request_with_retry(
        url,
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
    )
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "lxml")

    notices = []

    for item in soup.select(item_selector):
        title_tag = item.select_one(title_selector)

        if title_tag is None:
            continue

        title = title_tag.get_text(strip=True)

        href = title_tag.get("href", "")
        link = urljoin(url, href)

        if date_selector:
            date_tag = item.select_one(date_selector)
            if date_tag:
                date = date_tag.get_text(strip=True)
                if not date:
                    date = (
                        date_tag.get("data-date")
                        or date_tag.get("datetime")
                        or date_tag.get("title")
                        or ""
                    )
            else:
                date = ""
        else:
            text = item.get_text(" ", strip=True)
            match = re.search(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", text)
            date = match.group(0) if match else ""

        notices.append({
            "title": title,
            "link": link,
            "date": date,
        })

    return notices


def get_article_text(
    url,
    content_selector=None,
    max_attempts=3,
    backoff_seconds=(2, 4, 8),
):
    response = request_with_retry(
        url,
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
    )
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "lxml")

    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    if content_selector:
        content = soup.select_one(content_selector)
    else:
        common_selectors = [
            ".article",
            ".article-content",
            ".content",
            ".main-content",
            ".news-content",
            ".v_news_content",
            "#content",
            "#article",
            "article",
        ]

        content = None

        for selector in common_selectors:
            content = soup.select_one(selector)
            if content:
                break

        if content is None:
            content = soup.body

    if content is None:
        return ""

    text = content.get_text("\n", strip=True)

    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            lines.append(line)

    return "\n".join(lines)

from urllib.parse import urljoin
import re

import requests
from bs4 import BeautifulSoup


def get_school_notices(url, item_selector, title_selector="a", date_selector=None):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
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


def get_article_text(url, content_selector=None):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
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

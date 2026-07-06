import json

import requests


def summarize_article_with_local_llm(
    title,
    body,
    model="qwen2.5:1.5b",
    ollama_base_url="http://localhost:11434",
    max_chars=12000,
):
    body = body[:max_chars]

    schema = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string"
            },
            "key_points": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "required": ["summary", "key_points"],
    }

    prompt = f"""
请阅读下面这篇学校通知公告，返回 JSON。

要求：
1. summary：一句话概括。
2. key_points：提取 3 到 6 条要点。
3. 只返回 JSON，不要 Markdown，不要解释。

标题：
{title}

正文：
{body}
"""

    url = f"{ollama_base_url.rstrip('/')}/api/chat"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个擅长总结学校通知公告的中文助手。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
        "format": schema,
        "options": {
            "temperature": 0.2,
        },
    }

    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()

    data = response.json()
    content = data["message"]["content"]

    return json.loads(content)


def fallback_summary(title, body, max_summary_chars=120):
    clean_body = " ".join(body.split())

    if not clean_body:
        return {
            "summary": title,
            "key_points": [],
        }

    summary = clean_body[:max_summary_chars]

    if len(clean_body) > max_summary_chars:
        summary += "..."

    return {
        "summary": summary,
        "key_points": [
            summary,
        ],
    }


def summarize_article(title, body, summary_config):
    engine = summary_config.get("engine", "ollama")

    if engine == "fallback":
        return fallback_summary(title, body)

    if engine != "ollama":
        raise ValueError(f"暂不支持的总结引擎：{engine}")

    ollama_config = summary_config.get("ollama", {})

    return summarize_article_with_local_llm(
        title=title,
        body=body,
        model=ollama_config.get("model", "qwen2.5:1.5b"),
        ollama_base_url=ollama_config.get("base_url", "http://localhost:11434"),
    )


def summarize_article_safe(title, body, summary_config):
    try:
        return summarize_article(title, body, summary_config)
    except Exception as e:
        print("AI 总结失败，改用正文开头作为摘要：", e)
        return fallback_summary(title, body)

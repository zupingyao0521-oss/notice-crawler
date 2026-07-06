from pathlib import Path
import os
import smtplib
import sys
import traceback
import re

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from notice_crawler.config_loader import get_sites_from_config, load_config
from notice_crawler.classifier import classify_article, sort_articles_by_importance
from notice_crawler.crawler import FetchError, get_article_text, get_school_notices
from notice_crawler.excel_writer import save_articles_to_excel
from notice_crawler.mailer import send_alert_email, send_email_with_excel
from notice_crawler.state import ProcessedArticleStore
from notice_crawler.summarizer import summarize_article_safe


def resolve_project_path(path_text):
    path = Path(path_text)

    if path.is_absolute():
        return path

    return BASE_DIR / path


def failure_record(kind, name, url, error):
    return {
        "kind": kind,
        "name": name,
        "url": url,
        "error": str(getattr(error, "last_error", error)),
        "attempts": getattr(error, "attempts", 1),
    }


def notice_date_key(notice):
    numbers = re.findall(r"\d+", str(notice.get("date", "")))
    if len(numbers) >= 3:
        return tuple(map(int, numbers[:3]))
    return (0, 0, 0)


def collect_new_notices(sites, processed_links, retry_config, force_latest=False):
    new_notices = []
    failures = []

    for site in sites:
        print(f"开始抓取：{site['name']} - {site['list_url']}")

        try:
            notices = get_school_notices(
                url=site["list_url"],
                item_selector=site["item_selector"],
                title_selector=site["title_selector"],
                date_selector=site["date_selector"],
                **retry_config,
            )
        except FetchError as error:
            print(f"列表页抓取彻底失败：{site['name']} - {error}")
            failures.append(failure_record(
                "网站列表",
                site["name"],
                site["list_url"],
                error,
            ))
            continue
        except Exception as error:
            print(f"列表页解析失败：{site['name']} - {error}")
            failures.append(failure_record(
                "网站列表",
                site["name"],
                site["list_url"],
                error,
            ))
            continue

        print(f"抓到 {len(notices)} 条通知")

        for notice in notices:
            link = notice["link"]

            if not force_latest and link in processed_links:
                continue

            notice["site_name"] = site["name"]
            notice["content_selector"] = site["content_selector"]
            new_notices.append(notice)

    if force_latest and new_notices:
        newest = max(
            enumerate(new_notices),
            key=lambda item: (notice_date_key(item[1]), -item[0]),
        )[1]
        return [newest], failures

    return new_notices, failures


def build_articles(new_notices, summary_config, retry_config):
    articles = []
    failures = []

    for notice in new_notices:
        title = notice["title"]
        link = notice["link"]

        print(f"处理新文章：{title}")

        try:
            body = get_article_text(
                link,
                content_selector=notice["content_selector"],
                **retry_config,
            )
        except FetchError as error:
            print(f"正文抓取彻底失败，跳过：{title} - {error}")
            failures.append(failure_record("文章正文", title, link, error))
            continue
        except Exception as error:
            print(f"正文解析失败，跳过：{title} - {error}")
            failures.append(failure_record("文章正文", title, link, error))
            continue

        summary_result = summarize_article_safe(
            title=title,
            body=body,
            summary_config=summary_config,
        )

        article = {
            "title": title,
            "link": link,
            "date": notice.get("date", ""),
            "site_name": notice.get("site_name", ""),
            "summary": summary_result["summary"],
            "key_points": summary_result["key_points"],
        }
        articles.append(classify_article(article, body=body))

    return sort_articles_by_importance(articles), failures


def send_failure_alert(failures, success_count, email_config):
    if not failures:
        return

    try:
        send_alert_email(
            to_emails=email_config["recipients"],
            failures=failures,
            success_count=success_count,
            sender_env=email_config.get("sender_env", "QQ_EMAIL"),
            auth_code_env=email_config.get("auth_code_env", "QQ_EMAIL_AUTH_CODE"),
        )
        print("抓取失败报警邮件已发送")
    except Exception:
        print("报警邮件发送失败：")
        traceback.print_exc()


def main():
    config = load_config(BASE_DIR / "config.yaml")
    sites = get_sites_from_config(config)
    retry_section = config.get("retry", {})
    retry_config = {
        "max_attempts": retry_section.get("max_attempts", 3),
        "backoff_seconds": retry_section.get("backoff_seconds", [2, 4, 8]),
    }
    email_config = config["email"]
    force_latest = os.environ.get("FORCE_LATEST_NOTICE", "").lower() == "true"

    state_config = config.get("state", {})
    database_path = resolve_project_path(
        state_config.get("database_path", "data/notice_crawler.db")
    )
    legacy_json_path = resolve_project_path(
        state_config.get("legacy_json_path", "data/processed_links.json")
    )
    excel_path = resolve_project_path(config["output"]["excel_path"])

    article_store = ProcessedArticleStore(
        database_path=database_path,
        legacy_json_path=legacy_json_path,
    )
    processed_links = article_store.load_links()

    new_notices, failures = collect_new_notices(
        sites=sites,
        processed_links=processed_links,
        retry_config=retry_config,
        force_latest=force_latest,
    )

    if not new_notices:
        send_failure_alert(failures, success_count=0, email_config=email_config)
        print("本次没有新文章，程序结束，不生成 Excel，也不发送邮件。")
        return

    print(f"本次发现 {len(new_notices)} 篇新文章")

    articles, article_failures = build_articles(
        new_notices=new_notices,
        summary_config=config["summary"],
        retry_config=retry_config,
    )
    failures.extend(article_failures)

    if not articles:
        send_failure_alert(failures, success_count=0, email_config=email_config)
        print("新文章都没有成功处理，程序结束，不发送空邮件。")
        return

    save_articles_to_excel(
        articles=articles,
        file_path=excel_path,
    )
    print(f"Excel 已生成：{excel_path}")

    sender_env = email_config.get("sender_env", "QQ_EMAIL")
    auth_code_env = email_config.get("auth_code_env", "QQ_EMAIL_AUTH_CODE")

    if not os.environ.get(sender_env):
        raise RuntimeError(f"缺少环境变量：{sender_env}，请先在 PowerShell 里设置发件邮箱")

    if not os.environ.get(auth_code_env):
        raise RuntimeError(f"缺少环境变量：{auth_code_env}，请先在 PowerShell 里设置 QQ 邮箱授权码")

    try:
        send_email_with_excel(
            to_emails=email_config["recipients"],
            subject=email_config.get("subject", "学校通知公告汇总"),
            articles=articles,
            excel_path=excel_path,
            sender_env=sender_env,
            auth_code_env=auth_code_env,
        )
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError("邮件登录失败：请检查 QQ 邮箱是否已开启 SMTP，以及授权码是否正确") from e
    except smtplib.SMTPException as e:
        raise RuntimeError(f"SMTP 发送失败：{e}") from e

    print("邮件已发送")

    send_failure_alert(
        failures,
        success_count=len(articles),
        email_config=email_config,
    )

    inserted_count = article_store.add_articles(articles)
    print(
        f"已写入 {inserted_count} 条浏览记录，"
        f"数据库共 {article_store.count()} 条：{database_path}"
    )


if __name__ == "__main__":
    main()

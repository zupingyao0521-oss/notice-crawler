from pathlib import Path
import os
import smtplib
import sys

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from notice_crawler.config_loader import get_sites_from_config, load_config
from notice_crawler.crawler import get_article_text, get_school_notices
from notice_crawler.excel_writer import save_articles_to_excel
from notice_crawler.mailer import send_email_with_excel
from notice_crawler.state import load_processed_links, save_processed_links
from notice_crawler.summarizer import summarize_article_safe


def resolve_project_path(path_text):
    path = Path(path_text)

    if path.is_absolute():
        return path

    return BASE_DIR / path


def collect_new_notices(sites, processed_links):
    new_notices = []

    for site in sites:
        print(f"开始抓取：{site['name']} - {site['list_url']}")

        notices = get_school_notices(
            url=site["list_url"],
            item_selector=site["item_selector"],
            title_selector=site["title_selector"],
            date_selector=site["date_selector"],
        )

        print(f"抓到 {len(notices)} 条通知")

        for notice in notices:
            link = notice["link"]

            if link in processed_links:
                continue

            notice["site_name"] = site["name"]
            notice["content_selector"] = site["content_selector"]
            new_notices.append(notice)

    return new_notices


def build_articles(new_notices, summary_config):
    articles = []

    for notice in new_notices:
        title = notice["title"]
        link = notice["link"]

        print(f"处理新文章：{title}")

        try:
            body = get_article_text(
                link,
                content_selector=notice["content_selector"],
            )
        except Exception as e:
            print(f"正文抓取失败，跳过：{title} - {e}")
            continue

        summary_result = summarize_article_safe(
            title=title,
            body=body,
            summary_config=summary_config,
        )

        articles.append({
            "title": title,
            "link": link,
            "date": notice.get("date", ""),
            "summary": summary_result["summary"],
            "key_points": summary_result["key_points"],
        })

    return articles


def main():
    config = load_config(BASE_DIR / "config.yaml")
    sites = get_sites_from_config(config)

    processed_links_path = resolve_project_path(
        config.get("state", {}).get("processed_links_path", "processed_links.json")
    )
    excel_path = resolve_project_path(config["output"]["excel_path"])

    processed_links = load_processed_links(processed_links_path)

    new_notices = collect_new_notices(
        sites=sites,
        processed_links=processed_links,
    )

    if not new_notices:
        print("本次没有新文章，程序结束，不生成 Excel，也不发送邮件。")
        return

    print(f"本次发现 {len(new_notices)} 篇新文章")

    articles = build_articles(
        new_notices=new_notices,
        summary_config=config["summary"],
    )

    if not articles:
        print("新文章都没有成功处理，程序结束，不发送空邮件。")
        return

    save_articles_to_excel(
        articles=articles,
        file_path=excel_path,
    )
    print(f"Excel 已生成：{excel_path}")

    email_config = config["email"]

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

    processed_links.update(article["link"] for article in articles)
    save_processed_links(processed_links, processed_links_path)
    print(f"已更新去重记录：{processed_links_path}")


if __name__ == "__main__":
    main()

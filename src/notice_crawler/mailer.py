import html
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path


def build_articles_html(articles):
    rows = []

    for article in articles:
        title = html.escape(article.get("title", ""))
        link = html.escape(article.get("link", ""))
        date = html.escape(article.get("date", ""))
        summary = html.escape(article.get("summary", ""))

        key_points = article.get("key_points", [])
        key_points_html = "".join(
            f"<li>{html.escape(str(point))}</li>"
            for point in key_points
        )

        rows.append(f"""
        <tr>
            <td>{title}</td>
            <td>{date}</td>
            <td>{summary}</td>
            <td><ul>{key_points_html}</ul></td>
            <td><a href="{link}">查看原文</a></td>
        </tr>
        """)

    return f"""
    <html>
    <body>
        <h2>学校通知公告汇总</h2>
        <p>以下是本次抓取并总结的文章列表：</p>

        <table border="1" cellpadding="8" cellspacing="0">
            <thead>
                <tr>
                    <th>标题</th>
                    <th>发布日期</th>
                    <th>一句话概括</th>
                    <th>要点</th>
                    <th>链接</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </body>
    </html>
    """


def send_email_with_excel(
    to_emails,
    subject,
    articles,
    excel_path,
    sender_env="QQ_EMAIL",
    auth_code_env="QQ_EMAIL_AUTH_CODE",
):
    sender_email = os.environ[sender_env]
    auth_code = os.environ[auth_code_env]

    if isinstance(to_emails, str):
        to_emails = [to_emails]

    excel_path = Path(excel_path)

    message = EmailMessage()
    message["From"] = formataddr(("学校通知机器人", sender_email))
    message["To"] = ", ".join(to_emails)
    message["Subject"] = subject

    message.set_content("你的邮箱客户端不支持 HTML，请查看附件中的 Excel 文件。")

    html_body = build_articles_html(articles)
    message.add_alternative(html_body, subtype="html")

    with excel_path.open("rb") as f:
        excel_data = f.read()

    message.add_attachment(
        excel_data,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=excel_path.name,
    )

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as smtp:
        smtp.login(sender_email, auth_code)
        smtp.send_message(message)

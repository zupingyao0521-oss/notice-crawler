import html
import os
import smtplib
import platform
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path


BEIJING_TIMEZONE = timezone(timedelta(hours=8), name="CST")


def build_articles_html(articles):
    article_sections = []

    for index, article in enumerate(articles, start=1):
        title = html.escape(article.get("title", ""))
        link = html.escape(article.get("link", ""), quote=True)
        date = html.escape(article.get("date", ""))
        summary = html.escape(article.get("summary", ""))
        importance = html.escape(article.get("importance", "一般"))
        tags = article.get("tags", ["其他"])
        tags_text = " · ".join(html.escape(str(tag)) for tag in tags)
        importance_color = {
            "紧急": "#dc2626",
            "重要": "#d97706",
            "一般": "#64748b",
        }.get(article.get("importance"), "#64748b")

        key_points = article.get("key_points", [])
        key_points_html = "".join(
            f"""
            <tr>
              <td style="width:18px;padding:3px 0;vertical-align:top;color:#2563eb;font-size:15px;line-height:22px;">&#8226;</td>
              <td style="padding:3px 0;color:#334155;font-size:14px;line-height:22px;">{html.escape(str(point))}</td>
            </tr>
            """
            for point in key_points
        )
        if not key_points_html:
            key_points_html = """
            <tr>
              <td style="padding:3px 0;color:#64748b;font-size:14px;line-height:22px;">暂无提炼要点</td>
            </tr>
            """

        article_sections.append(f"""
        <tr>
          <td style="padding:0 32px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
              <tr>
                <td style="padding:26px 0 8px;vertical-align:top;">
                  <span style="display:inline-block;margin-right:8px;color:#2563eb;font-size:13px;font-weight:700;line-height:20px;">{index:02d}</span>
                  <span style="display:inline-block;margin-right:8px;color:{importance_color};font-size:13px;font-weight:700;line-height:20px;">{importance}</span>
                  <span style="color:#64748b;font-size:13px;line-height:20px;">{date or '日期未注明'} &nbsp;|&nbsp; {tags_text}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:0;color:#0f172a;font-size:19px;font-weight:700;line-height:28px;">{title}</td>
              </tr>
              <tr>
                <td style="padding:14px 0 0;">
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;background-color:#f8fafc;border-left:4px solid #2563eb;">
                    <tr>
                      <td style="padding:14px 16px;color:#334155;font-size:14px;line-height:23px;">{summary or '暂无摘要'}</td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:16px 0 5px;color:#0f172a;font-size:13px;font-weight:700;line-height:20px;">通知要点</td>
              </tr>
              <tr>
                <td>
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
                    {key_points_html}
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:18px 0 26px;">
                  <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
                    <tr>
                      <td bgcolor="#2563eb" style="background-color:#2563eb;">
                        <a href="{link}" style="display:inline-block;padding:10px 18px;color:#ffffff;font-size:14px;font-weight:700;line-height:20px;text-decoration:none;">查看通知原文&nbsp;&rarr;</a>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td height="1" style="height:1px;background-color:#e2e8f0;font-size:0;line-height:0;">&nbsp;</td>
              </tr>
            </table>
          </td>
        </tr>
        """)

    return f"""
    <!doctype html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>学校通知公告汇总</title>
    </head>
    <body style="margin:0;padding:0;background-color:#eef2f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',Arial,sans-serif;">
      <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">本次共整理 {len(articles)} 条学校通知，摘要与重点已为你归纳。</div>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;background-color:#eef2f7;">
        <tr>
          <td align="center" style="padding:28px 12px;">
            <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;border-collapse:collapse;background-color:#ffffff;">
              <tr>
                <td bgcolor="#0f172a" style="padding:34px 32px;background-color:#0f172a;">
                  <div style="color:#93c5fd;font-size:12px;font-weight:700;line-height:18px;">DAILY NOTICE DIGEST</div>
                  <div style="padding-top:7px;color:#ffffff;font-size:27px;font-weight:700;line-height:36px;">学校通知公告汇总</div>
                  <div style="padding-top:9px;color:#cbd5e1;font-size:14px;line-height:22px;">本次共发现 <strong style="color:#ffffff;">{len(articles)}</strong> 条新通知，重要信息已整理如下。</div>
                </td>
              </tr>
              {''.join(article_sections)}
              <tr>
                <td align="center" style="padding:24px 32px 30px;color:#64748b;font-size:12px;line-height:20px;">
                  完整数据已附在 Excel 文件中<br>
                  此邮件由 Notice Crawler 自动整理并发送
                </td>
              </tr>
            </table>
          </td>
        </tr>
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


def build_alert_bodies(failures, success_count, environment=None, now=None):
    now = now or datetime.now(BEIJING_TIMEZONE)
    if environment is None:
        runtime = f"{platform.system()} / Python {platform.python_version()}"
        environment = f"GitHub Actions ({runtime})" if os.environ.get("GITHUB_ACTIONS") else runtime
    failed_count = len(failures)
    failure_time = now.strftime("%Y-%m-%d %H:%M:%S %Z")

    text_sections = []
    html_sections = []
    for index, failure in enumerate(failures, start=1):
        name = str(failure.get("name", "未知目标"))
        url = str(failure.get("url", ""))
        error = str(failure.get("error", "未知错误"))
        attempts = int(failure.get("attempts", 1))
        kind = str(failure.get("kind", "抓取任务"))
        text_sections.append(
            f"{index}. [{kind}] {name}\n"
            f"   URL: {url}\n"
            f"   错误: {error}\n"
            f"   尝试次数: {attempts}"
        )
        html_sections.append(f"""
        <tr><td style="padding:18px 0;border-top:1px solid #fecaca;">
          <div style="color:#991b1b;font-size:15px;font-weight:700;">{index}. [{html.escape(kind)}] {html.escape(name)}</div>
          <div style="padding-top:8px;color:#475569;font-size:13px;line-height:21px;word-break:break-all;">
            <strong>网址：</strong>{html.escape(url)}<br>
            <strong>错误：</strong>{html.escape(error)}<br>
            <strong>尝试次数：</strong>{attempts}
          </div>
        </td></tr>
        """)

    text_body = (
        "Notice Crawler 抓取任务出现失败。\n\n"
        f"失败时间：{failure_time}\n"
        f"运行环境：{environment}\n"
        f"成功数量：{success_count}\n"
        f"失败数量：{failed_count}\n\n"
        + "\n\n".join(text_sections)
    )
    html_body = f"""
    <!doctype html><html lang="zh-CN"><body style="margin:0;background:#fef2f2;font-family:Arial,'Microsoft YaHei',sans-serif;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px;">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#ffffff;border-collapse:collapse;">
          <tr><td style="padding:28px 30px;background:#991b1b;color:#ffffff;">
            <div style="font-size:12px;font-weight:700;">NOTICE CRAWLER ALERT</div>
            <div style="padding-top:6px;font-size:24px;font-weight:700;">通知抓取失败</div>
          </td></tr>
          <tr><td style="padding:24px 30px;color:#334155;font-size:14px;line-height:23px;">
            <strong>失败时间：</strong>{html.escape(failure_time)}<br>
            <strong>运行环境：</strong>{html.escape(environment)}<br>
            <strong>成功数量：</strong>{success_count}<br>
            <strong>失败数量：</strong>{failed_count}
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:18px;border-collapse:collapse;">{''.join(html_sections)}</table>
          </td></tr>
        </table>
      </td></tr></table>
    </body></html>
    """
    return text_body, html_body


def send_alert_email(
    to_emails,
    failures,
    success_count,
    sender_env="QQ_EMAIL",
    auth_code_env="QQ_EMAIL_AUTH_CODE",
):
    sender_email = os.environ[sender_env]
    auth_code = os.environ[auth_code_env]
    if isinstance(to_emails, str):
        to_emails = [to_emails]

    text_body, html_body = build_alert_bodies(failures, success_count)
    message = EmailMessage()
    message["From"] = formataddr(("Notice Crawler 报警", sender_email))
    message["To"] = ", ".join(to_emails)
    message["Subject"] = "【Notice Crawler 报警】通知抓取失败"
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as smtp:
        smtp.login(sender_email, auth_code)
        smtp.send_message(message)

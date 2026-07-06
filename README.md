# Notice Crawler

一个用于抓取学校通知公告、去重、提取正文、调用本地大模型总结、生成 Excel 并通过 QQ 邮箱发送附件的 Python 小项目。

## 功能

- 抓取通知公告列表页中的标题、链接和发布日期
- 自动跳过已经处理过的文章链接
- 抓取文章正文纯文字
- 使用 Ollama 本地大模型生成一句话概括和要点
- 当总结引擎失败时，自动截取正文开头作为兜底摘要
- 生成带可点击链接的 Excel 文件
- 通过 QQ 邮箱 SMTP 发送 HTML 正文和 Excel 附件
- 如果本次没有新文章，直接结束，不发送空邮件

## 目录结构

```text
.
├─ main.py
├─ config.example.yaml
├─ requirements.txt
└─ src/
   └─ notice_crawler/
      ├─ config_loader.py
      ├─ crawler.py
      ├─ excel_writer.py
      ├─ mailer.py
      ├─ state.py
      └─ summarizer.py
```

## 安装依赖

```bash
python -m pip install -r requirements.txt
```

如果使用 Ollama 本地大模型，请先安装 Ollama，并下载模型：

```bash
ollama pull qwen2.5:1.5b
```

## 配置

复制配置模板：

```powershell
copy .\config.example.yaml .\config.yaml
```

然后编辑 `config.yaml`：

- `sites`：配置要抓取的网站列表
- `recipients`：配置收件邮箱
- `summary.ollama.model`：配置 Ollama 模型
- `defaults`：配置网页 CSS 选择器

真实的 `config.yaml` 已被 `.gitignore` 忽略，不建议提交到 GitHub。

## 邮箱授权码

QQ 邮箱 SMTP 授权码不能写进代码，也不能提交到 GitHub。运行前在 PowerShell 中设置环境变量：

```powershell
$env:QQ_EMAIL="你的QQ邮箱@qq.com"
$env:QQ_EMAIL_AUTH_CODE="你的QQ邮箱SMTP授权码"
```

如果授权码泄露，请立即到 QQ 邮箱重新生成。

## 运行

```powershell
python .\main.py
```

运行后：

- Excel 文件默认生成到 `outputs/学校通知汇总.xlsx`
- 已处理链接默认记录到 `data/processed_links.json`
- 如果没有新文章，程序不会发送邮件

## 注意

请遵守目标网站的访问规则，不要高频请求，也不要抓取不允许抓取的内容。

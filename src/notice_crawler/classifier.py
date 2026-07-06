import re
from datetime import datetime


TAG_RULES = {
    "考试": ("考试", "考场", "准考证", "补考", "缓考", "成绩"),
    "选课": ("选课", "退课", "补选", "课程调整"),
    "报名": ("报名", "申报", "申请", "征集"),
    "奖助": ("奖学金", "助学金", "资助", "评优", "评奖"),
    "就业": ("招聘", "就业", "实习", "双选会", "宣讲会"),
    "讲座": ("讲座", "论坛", "学术报告", "交流会"),
    "竞赛": ("竞赛", "比赛", "大赛", "赛事"),
    "教学": ("教学", "培养方案", "实训", "实践", "毕业论文", "答辩"),
    "放假": ("放假", "假期", "调休", "返校", "开学"),
    "缴费": ("缴费", "交费", "学费", "费用"),
    "公示": ("公示", "名单", "结果公布"),
}

URGENT_KEYWORDS = (
    "紧急", "截止今日", "今日截止", "最后一天", "停课", "考试安排",
    "补考", "缓考", "准考证", "缴费截止", "逾期不予", "务必",
)

IMPORTANT_KEYWORDS = (
    "重要", "截止", "考试", "报名", "申报", "申请", "选课", "补选",
    "答辩", "返校", "开学", "放假", "缴费", "公示", "招聘",
)


def _article_text(article, body=""):
    key_points = article.get("key_points", [])
    if isinstance(key_points, list):
        key_points = " ".join(str(point) for point in key_points)

    return " ".join([
        str(article.get("title", "")),
        str(article.get("summary", "")),
        str(key_points),
        str(body),
    ])


def classify_article(article, body=""):
    """Return a copy of an article enriched with tags and importance."""
    text = _article_text(article, body)
    tags = [
        tag
        for tag, keywords in TAG_RULES.items()
        if any(keyword in text for keyword in keywords)
    ]

    if any(keyword in text for keyword in URGENT_KEYWORDS):
        importance = "紧急"
        importance_score = 3
    elif any(keyword in text for keyword in IMPORTANT_KEYWORDS):
        importance = "重要"
        importance_score = 2
    else:
        importance = "一般"
        importance_score = 1

    enriched = dict(article)
    enriched["tags"] = tags or ["其他"]
    enriched["importance"] = importance
    enriched["importance_score"] = importance_score
    return enriched


def _date_sort_value(date_text):
    numbers = re.findall(r"\d+", str(date_text))
    if len(numbers) < 3:
        return 0

    try:
        return int(datetime(*map(int, numbers[:3])).strftime("%Y%m%d"))
    except ValueError:
        return 0


def sort_articles_by_importance(articles):
    """Sort urgent articles first, then newer articles, preserving stable ties."""
    return sorted(
        articles,
        key=lambda article: (
            article.get("importance_score", 1),
            _date_sort_value(article.get("date", "")),
        ),
        reverse=True,
    )

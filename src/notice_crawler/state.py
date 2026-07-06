import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class ProcessedArticleStore:
    def __init__(self, database_path, legacy_json_path=None):
        self.database_path = Path(database_path)
        self.legacy_json_path = Path(legacy_json_path) if legacy_json_path else None
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        self._migrate_legacy_json()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self):
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS processed_articles (
                    url TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '',
                    source_name TEXT NOT NULL DEFAULT '',
                    published_date TEXT NOT NULL DEFAULT '',
                    processed_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_articles_processed_at
                ON processed_articles(processed_at)
            """)

    def _migrate_legacy_json(self):
        path = self.legacy_json_path
        if path is None or not path.exists():
            return 0

        with path.open("r", encoding="utf-8") as file:
            links = json.load(file)

        records = [{"link": link} for link in links if link]
        return self.add_articles(records)

    def load_links(self):
        with self._connect() as connection:
            rows = connection.execute("SELECT url FROM processed_articles").fetchall()
        return {row["url"] for row in rows}

    def contains(self, url):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM processed_articles WHERE url = ? LIMIT 1",
                (url,),
            ).fetchone()
        return row is not None

    def add_articles(self, articles):
        processed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        records = [
            (
                str(article.get("link", "")),
                str(article.get("title", "")),
                str(article.get("site_name", "")),
                str(article.get("date", "")),
                processed_at,
            )
            for article in articles
            if article.get("link")
        ]
        if not records:
            return 0

        with self._connect() as connection:
            before = connection.total_changes
            connection.executemany("""
                INSERT OR IGNORE INTO processed_articles (
                    url, title, source_name, published_date, processed_at
                ) VALUES (?, ?, ?, ?, ?)
            """, records)
            return connection.total_changes - before

    def count(self):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM processed_articles"
            ).fetchone()
        return row["count"]

import os
import sqlite3
import threading
from collections import Counter, defaultdict


class Storage:
    def __init__(self, db_path: str = "data/crawler.db") -> None:
        self.db_path = db_path
        self.storage_dir = "data/storage"
        self.lock = threading.RLock()
        self.queued_urls: set[str] = set()
        self.frontier_snapshot: list[dict] = []

        self._ensure_dirs()
        self._init_db()
        self.frontier_snapshot = self.load_frontier_snapshot()
        self._rebuild_storage_files()

    def _ensure_dirs(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        os.makedirs(self.storage_dir, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS visited_urls (
                    url TEXT PRIMARY KEY
                );

                CREATE TABLE IF NOT EXISTS pages (
                    url TEXT PRIMARY KEY,
                    origin_url TEXT NOT NULL,
                    depth INTEGER NOT NULL,
                    title TEXT,
                    body TEXT
                );

                CREATE TABLE IF NOT EXISTS tokens (
                    term TEXT NOT NULL,
                    url TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    is_title INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (term, url, is_title),
                    FOREIGN KEY (url) REFERENCES pages(url)
                );

                CREATE TABLE IF NOT EXISTS frontier (
                    url TEXT PRIMARY KEY,
                    origin_url TEXT NOT NULL,
                    depth INTEGER NOT NULL,
                    max_depth INTEGER NOT NULL
                );
                """
            )

    def mark_queued(self, url: str) -> None:
        with self.lock:
            self.queued_urls.add(url)

    def unmark_queued(self, url: str) -> None:
        with self.lock:
            self.queued_urls.discard(url)

    def has_visited(self, url: str) -> bool:
        with self.lock, self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM visited_urls WHERE url = ? LIMIT 1",
                (url,),
            ).fetchone()
            return row is not None

    def is_seen_or_queued(self, url: str) -> bool:
        with self.lock:
            if url in self.queued_urls:
                return True
        return self.has_visited(url)

    def mark_visited(self, url: str) -> None:
        with self.lock, self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO visited_urls(url) VALUES (?)",
                (url,),
            )

    def store_page(
        self,
        url: str,
        origin_url: str,
        depth: int,
        title: str,
        body: str,
        body_tokens: list[str],
        title_tokens: list[str],
    ) -> None:
        body_counts = dict(Counter(body_tokens))
        title_counts = dict(Counter(title_tokens))

        with self.lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO pages(url, origin_url, depth, title, body)
                VALUES (?, ?, ?, ?, ?)
                """,
                (url, origin_url, depth, title, body),
            )

            conn.execute("DELETE FROM tokens WHERE url = ?", (url,))

            for term, count in body_counts.items():
                conn.execute(
                    """
                    INSERT OR REPLACE INTO tokens(term, url, count, is_title)
                    VALUES (?, ?, ?, 0)
                    """,
                    (term, url, count),
                )

            for term, count in title_counts.items():
                conn.execute(
                    """
                    INSERT OR REPLACE INTO tokens(term, url, count, is_title)
                    VALUES (?, ?, ?, 1)
                    """,
                    (term, url, count),
                )

        self._rebuild_storage_files()

    def _word_file_name(self, token: str) -> str:
        first = token[0].lower()
        if not first.isalpha():
            first = "other"
        return os.path.join(self.storage_dir, f"{first}.data")

    def _rebuild_storage_files(self) -> None:
        for name in os.listdir(self.storage_dir):
            if name.endswith(".data"):
                try:
                    os.remove(os.path.join(self.storage_dir, name))
                except OSError:
                    pass

        file_lines: dict[str, list[str]] = defaultdict(list)

        with self.lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT t.term, p.url, p.origin_url, p.depth, SUM(t.count) as total_frequency
                FROM tokens t
                JOIN pages p ON t.url = p.url
                GROUP BY t.term, p.url, p.origin_url, p.depth
                """
            ).fetchall()

        for term, url, origin_url, depth, frequency in rows:
            line = f"{term} {url} {origin_url} {depth} {frequency}"
            file_lines[self._word_file_name(term)].append(line)

        for filename, lines in file_lines.items():
            with open(filename, "w", encoding="utf-8") as handle:
                for line in sorted(lines):
                    handle.write(line + "\n")

    def get_page_count(self) -> int:
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM pages").fetchone()
            return int(row[0])

    def get_visited_count(self) -> int:
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM visited_urls").fetchone()
            return int(row[0])

    def get_result_metadata(self, url: str) -> tuple[str, int] | None:
        with self.lock, self._connect() as conn:
            row = conn.execute(
                "SELECT origin_url, depth FROM pages WHERE url = ?",
                (url,),
            ).fetchone()
            return row if row else None

    def search(self, tokens: list[str]) -> list[tuple[str, float]]:
        scores: dict[str, float] = defaultdict(float)

        with self.lock, self._connect() as conn:
            for term in tokens:
                rows = conn.execute(
                    "SELECT url, count, is_title FROM tokens WHERE term = ?",
                    (term,),
                ).fetchall()

                for url, count, is_title in rows:
                    if is_title:
                        scores[url] += float(count) * 3.0
                    else:
                        scores[url] += float(count)

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return ranked

    def load_frontier_snapshot(self) -> list[dict]:
        with self.lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT url, origin_url, depth, max_depth FROM frontier"
            ).fetchall()

        return [
            {
                "url": url,
                "origin_url": origin_url,
                "depth": depth,
                "max_depth": max_depth,
            }
            for url, origin_url, depth, max_depth in rows
        ]

    def save_frontier_snapshot(self, frontier_items: list[dict]) -> None:
        with self.lock, self._connect() as conn:
            conn.execute("DELETE FROM frontier")

            for item in frontier_items:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO frontier(url, origin_url, depth, max_depth)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        item["url"],
                        item["origin_url"],
                        item["depth"],
                        item["max_depth"],
                    ),
                )

    def clear(self) -> None:
        with self.lock:
            self.queued_urls.clear()
            self.frontier_snapshot.clear()

            with self._connect() as conn:
                conn.execute("DELETE FROM visited_urls")
                conn.execute("DELETE FROM pages")
                conn.execute("DELETE FROM tokens")
                conn.execute("DELETE FROM frontier")

        for name in os.listdir(self.storage_dir):
            if name.endswith(".data"):
                try:
                    os.remove(os.path.join(self.storage_dir, name))
                except OSError:
                    pass
import json
import os
import threading
from collections import Counter, defaultdict


class Storage:
    def __init__(self, state_path: str = "data/state.json") -> None:
        self.state_path = state_path
        self.storage_dir = "data/storage"
        self.lock = threading.RLock()

        self.visited_urls: set[str] = set()
        self.queued_urls: set[str] = set()
        self.frontier_snapshot: list[dict] = []

        self.pages: dict[str, dict] = {}
        self.body_index: dict[str, dict[str, int]] = defaultdict(dict)
        self.title_index: dict[str, dict[str, int]] = defaultdict(dict)

        self._ensure_dirs()
        self._load_state()
        self._rebuild_storage_files()

    def _ensure_dirs(self) -> None:
        state_dir = os.path.dirname(self.state_path)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)
        os.makedirs(self.storage_dir, exist_ok=True)

    def _load_state(self) -> None:
        if not os.path.exists(self.state_path):
            return

        try:
            with open(self.state_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            return

        with self.lock:
            self.visited_urls = set(data.get("visited_urls", []))
            self.pages = data.get("pages", {})
            self.frontier_snapshot = data.get("frontier", [])

            for url, page_data in self.pages.items():
                for token, count in page_data.get("body_counts", {}).items():
                    self.body_index[token][url] = count
                for token, count in page_data.get("title_counts", {}).items():
                    self.title_index[token][url] = count

    def save_state(self, frontier_items: list[dict]) -> None:
        with self.lock:
            payload = {
                "visited_urls": sorted(self.visited_urls),
                "pages": self.pages,
                "frontier": frontier_items,
            }

        with open(self.state_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def mark_queued(self, url: str) -> None:
        with self.lock:
            self.queued_urls.add(url)

    def unmark_queued(self, url: str) -> None:
        with self.lock:
            self.queued_urls.discard(url)

    def is_seen_or_queued(self, url: str) -> bool:
        with self.lock:
            return url in self.visited_urls or url in self.queued_urls

    def mark_visited(self, url: str) -> None:
        with self.lock:
            self.visited_urls.add(url)

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

        with self.lock:
            self.pages[url] = {
                "url": url,
                "origin_url": origin_url,
                "depth": depth,
                "title": title,
                "body": body,
                "body_counts": body_counts,
                "title_counts": title_counts,
            }

            for token, count in body_counts.items():
                self.body_index[token][url] = count

            for token, count in title_counts.items():
                self.title_index[token][url] = count

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

        for page in self.pages.values():
            combined_counts = Counter(page.get("body_counts", {}))
            combined_counts.update(page.get("title_counts", {}))

            for token, frequency in combined_counts.items():
                line = (
                    f"{token} {page['url']} {page['origin_url']} "
                    f"{page['depth']} {frequency}"
                )
                file_lines[self._word_file_name(token)].append(line)

        for filename, lines in file_lines.items():
            with open(filename, "w", encoding="utf-8") as handle:
                for line in sorted(lines):
                    handle.write(line + "\n")

    def get_page_count(self) -> int:
        with self.lock:
            return len(self.pages)

    def get_result_metadata(self, url: str) -> tuple[str, int] | None:
        with self.lock:
            page = self.pages.get(url)
            if not page:
                return None
            return page["origin_url"], page["depth"]

    def search(self, tokens: list[str]) -> list[tuple[str, float]]:
        scores: dict[str, float] = defaultdict(float)

        with self.lock:
            for token in tokens:
                for url, count in self.body_index.get(token, {}).items():
                    scores[url] += float(count)

                for url, count in self.title_index.get(token, {}).items():
                    scores[url] += float(count) * 3.0

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return ranked

    def clear(self) -> None:
        with self.lock:
            self.visited_urls.clear()
            self.queued_urls.clear()
            self.frontier_snapshot.clear()
            self.pages.clear()
            self.body_index.clear()
            self.title_index.clear()

        if os.path.exists(self.state_path):
            os.remove(self.state_path)

        for name in os.listdir(self.storage_dir):
            if name.endswith(".data"):
                try:
                    os.remove(os.path.join(self.storage_dir, name))
                except OSError:
                    pass
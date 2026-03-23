import queue
import threading
import time
from dataclasses import dataclass, asdict
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests

from core.parser import parse_html, tokenize
from core.storage import Storage


@dataclass(frozen=True)
class CrawlTask:
    url: str
    origin_url: str
    depth: int
    max_depth: int


class CrawlManager:
    def __init__(
        self,
        storage: Storage,
        worker_count: int = 3,
        queue_capacity: int = 500,
        requests_per_second: float = 2.0,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.storage = storage
        self.worker_count = worker_count
        self.timeout_seconds = timeout_seconds
        self.request_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0.0

        self.frontier: queue.Queue[CrawlTask] = queue.Queue(maxsize=queue_capacity)
        self.workers: list[threading.Thread] = []
        self.stop_event = threading.Event()
        self.state_lock = threading.RLock()

        self.started = False
        self.active_workers = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_error = ""
        self.last_request_at = 0.0

        self._restore_frontier()

    def _restore_frontier(self) -> None:
        for item in self.storage.frontier_snapshot:
            try:
                task = CrawlTask(**item)
                self.frontier.put_nowait(task)
                self.storage.mark_queued(task.url)
            except Exception:
                continue

    def start(self) -> None:
        with self.state_lock:
            if self.started:
                return
            self.started = True

            for index in range(self.worker_count):
                thread = threading.Thread(
                    target=self._worker_loop,
                    name=f"crawl-worker-{index}",
                    daemon=True,
                )
                self.workers.append(thread)
                thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        for thread in self.workers:
            thread.join(timeout=1.0)
        self._persist_snapshot()

    def submit(self, origin_url: str, max_depth: int) -> bool:
        task = CrawlTask(
            url=origin_url.strip(),
            origin_url=origin_url.strip(),
            depth=0,
            max_depth=max_depth,
        )
        return self._enqueue(task)

    def _enqueue(self, task: CrawlTask) -> bool:
        if not task.url:
            return False

        if self.storage.is_seen_or_queued(task.url):
            return False

        try:
            self.frontier.put(task, timeout=0.3)
        except queue.Full:
            return False

        self.storage.mark_queued(task.url)
        self._persist_snapshot()
        return True

    def _worker_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                task = self.frontier.get(timeout=0.5)
            except queue.Empty:
                continue

            with self.state_lock:
                self.active_workers += 1

            self.storage.unmark_queued(task.url)

            try:
                self._process_task(task)
            finally:
                with self.state_lock:
                    self.active_workers -= 1
                self.frontier.task_done()
                self._persist_snapshot()

    def _respect_rate_limit(self) -> None:
        if self.request_interval <= 0:
            return

        with self.state_lock:
            now = time.time()
            elapsed = now - self.last_request_at
            if elapsed < self.request_interval:
                time.sleep(self.request_interval - elapsed)
            self.last_request_at = time.time()

    def _process_task(self, task: CrawlTask) -> None:
        if self.storage.is_seen_or_queued(task.url) and task.url in self.storage.visited_urls:
            return

        self.storage.mark_visited(task.url)

        html = self._fetch(task.url)
        if html is None:
            with self.state_lock:
                self.failure_count += 1
            return

        title, body, links = parse_html(html, task.url)
        body_tokens = tokenize(body)
        title_tokens = tokenize(title)

        self.storage.store_page(
            url=task.url,
            origin_url=task.origin_url,
            depth=task.depth,
            title=title,
            body=body,
            body_tokens=body_tokens,
            title_tokens=title_tokens,
        )

        if task.depth < task.max_depth:
            for link in links:
                child = CrawlTask(
                    url=link,
                    origin_url=task.origin_url,
                    depth=task.depth + 1,
                    max_depth=task.max_depth,
                )
                self._enqueue(child)

        with self.state_lock:
            self.success_count += 1

    def _fetch(self, url: str) -> str | None:
        self._respect_rate_limit()

        try:
            response = requests.get(
                url,
                headers={"User-Agent": "BrightwaveCLI/1.0"},
                timeout=self.timeout_seconds,
                verify=False
            )
            if response.status_code != 200:
                self.last_error = f"HTTP {response.status_code} for {url}"
                return None

            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                self.last_error = f"Skipped non-HTML content at {url}"
                return None

            response.encoding = response.encoding or "utf-8"
            return response.text

        except requests.RequestException as exc:
            self.last_error = f"Request failed for {url}: {exc}"
            return None

    def _persist_snapshot(self) -> None:
        items: list[dict] = []

        with self.frontier.mutex:
            for task in list(self.frontier.queue):
                items.append(asdict(task))

        self.storage.frontier_snapshot = items
        self.storage.save_state(items)

    def status(self) -> dict:
        with self.state_lock:
            return {
                "queue_size": self.frontier.qsize(),
                "indexed_pages": self.storage.get_page_count(),
                "active_workers": self.active_workers,
                "crawler_active": self.active_workers > 0 or not self.frontier.empty(),
                "back_pressure_on": self.frontier.full(),
                "visited_urls": len(self.storage.visited_urls),
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "last_error": self.last_error,
                "worker_count": self.worker_count,
            }
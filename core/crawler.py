import queue
import threading
import time
from dataclasses import dataclass

import requests
import urllib3

from core.parser import parse_html, tokenize

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass(frozen=True)
class CrawlTask:
    url: str
    origin_url: str
    depth: int
    max_depth: int


class CrawlManager:
    def __init__(
        self,
        storage,
        worker_count: int = 3,
        queue_capacity: int = 500,
        requests_per_second: float = 2.0,
        timeout_seconds: float = 8.0,
    ):
        self.storage = storage
        self.worker_count = worker_count
        self.queue_capacity = queue_capacity
        self.requests_per_second = requests_per_second
        self.timeout_seconds = timeout_seconds

        self.frontier = queue.Queue(maxsize=queue_capacity)
        self.stop_event = threading.Event()
        self.threads: list[threading.Thread] = []

        self.active_workers = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_error = ""

        self.rate_delay = 1.0 / max(0.1, requests_per_second)
        self.lock = threading.RLock()

    def start(self):
        self.stop_event.clear()

        # Resume frontier if exists
        for item in self.storage.frontier_snapshot:
            task = CrawlTask(
                item["url"],
                item["origin_url"],
                item["depth"],
                item["max_depth"],
            )
            try:
                self.frontier.put_nowait(task)
                self.storage.mark_queued(task.url)
            except queue.Full:
                break

        self.threads = []
        for _ in range(self.worker_count):
            t = threading.Thread(target=self.worker_loop, daemon=True)
            t.start()
            self.threads.append(t)

    def stop(self):
        self.stop_event.set()

        # Save frontier snapshot for resume
        snapshot = []
        while not self.frontier.empty():
            try:
                task = self.frontier.get_nowait()
            except queue.Empty:
                break

            snapshot.append(
                {
                    "url": task.url,
                    "origin_url": task.origin_url,
                    "depth": task.depth,
                    "max_depth": task.max_depth,
                }
            )

        self.storage.save_frontier_snapshot(snapshot)

        for t in self.threads:
            t.join(timeout=1.0)

    def submit(self, url: str, max_depth: int) -> bool:
        if self.storage.is_seen_or_queued(url):
            return False

        task = CrawlTask(url, url, 0, max_depth)

        try:
            self.frontier.put_nowait(task)
            self.storage.mark_queued(url)
            return True
        except queue.Full:
            return False

    def worker_loop(self):
        while not self.stop_event.is_set():
            try:
                task = self.frontier.get(timeout=0.5)
            except queue.Empty:
                continue

            with self.lock:
                self.active_workers += 1

            try:
                processed = self.process_task(task)
                if processed:
                    with self.lock:
                        self.success_count += 1
            except Exception as e:
                with self.lock:
                    self.failure_count += 1
                    self.last_error = str(e)
            finally:
                self.storage.unmark_queued(task.url)
                with self.lock:
                    self.active_workers -= 1
                self.frontier.task_done()

            time.sleep(self.rate_delay)

    def process_task(self, task: CrawlTask) -> bool:
        if self.storage.has_visited(task.url):
            return False

        try:
            response = requests.get(
                task.url,
                timeout=self.timeout_seconds,
                headers={"User-Agent": "BrightwaveCLI/1.0"},
                verify=False,
            )
            html = response.text
        except Exception as e:
            raise Exception(f"Request failed for {task.url}: {e}")

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

        self.storage.mark_visited(task.url)

        if task.depth < task.max_depth:
            for link in links:
                if self.storage.is_seen_or_queued(link):
                    continue

                new_task = CrawlTask(
                    link,
                    task.origin_url,
                    task.depth + 1,
                    task.max_depth,
                )

                try:
                    self.frontier.put_nowait(new_task)
                    self.storage.mark_queued(link)
                except queue.Full:
                    break

        return True

    def status(self) -> dict:
        return {
            "queue_size": self.frontier.qsize(),
            "indexed_pages": self.storage.get_page_count(),
            "active_workers": self.active_workers,
            "crawler_active": self.active_workers > 0 or not self.frontier.empty(),
            "back_pressure_on": self.frontier.full(),
            "visited_urls": self.storage.get_visited_count(),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_error": self.last_error,
            "worker_count": self.worker_count,
        }
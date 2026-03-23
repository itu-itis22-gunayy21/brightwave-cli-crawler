from core.crawler import CrawlManager
from core.search import SearchEngine
from core.storage import Storage


HELP_TEXT = """
Commands
--------
index <url> <depth>     Start indexing from a seed URL
search <query>          Search indexed pages
status                  Show current system state
clear                   Clear saved state and indexed data
help                    Show help
exit                    Save and quit
""".strip()


def run_cli() -> None:
    storage = Storage("data/state.json")
    crawler = CrawlManager(
        storage=storage,
        worker_count=3,
        queue_capacity=500,
        requests_per_second=2.0,
        timeout_seconds=8.0,
    )
    search_engine = SearchEngine(storage)

    crawler.start()

    print("Brightwave CLI Crawler")
    print(HELP_TEXT)

    while True:
        try:
            raw = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaving state and shutting down...")
            crawler.stop()
            break

        if not raw:
            continue

        if raw == "help":
            print(HELP_TEXT)
            continue

        if raw == "status":
            snapshot = crawler.status()
            print("\nSystem status")
            for key, value in snapshot.items():
                print(f"  {key}: {value}")
            continue

        if raw == "clear":
            crawler.stop()
            storage.clear()
            print("Saved state cleared.")

            # Reinitialize system after clearing state
            storage = Storage("data/state.json")
            crawler = CrawlManager(
                storage=storage,
                worker_count=3,
                queue_capacity=500,
                requests_per_second=2.0,
                timeout_seconds=8.0,
            )
            search_engine = SearchEngine(storage)

            crawler.start()
            continue

        if raw == "exit":
            crawler.stop()
            print("Goodbye.")
            break

        if raw.startswith("index "):
            parts = raw.split(maxsplit=2)
            if len(parts) != 3:
                print("Usage: index <url> <depth>")
                continue

            url = parts[1]

            try:
                depth = int(parts[2])
            except ValueError:
                print("Depth must be an integer.")
                continue

            accepted = crawler.submit(url, depth)
            if accepted:
                print(f"Accepted crawl job for {url} with depth {depth}.")
            else:
                print("Job rejected: duplicate URL or queue is full.")
            continue

        if raw.startswith("search "):
            query = raw[len("search "):].strip()
            if not query:
                print("Usage: search <query>")
                continue

            results = search_engine.search(query)
            if not results:
                print("No results found.")
                continue

            print(f"\nFound {len(results)} result(s):")
            for relevant_url, origin_url, depth in results[:20]:
                print(f"  ({relevant_url}, {origin_url}, {depth})")
            continue

        print("Unknown command. Type 'help' to see available commands.")
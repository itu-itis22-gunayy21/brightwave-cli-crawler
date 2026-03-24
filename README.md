
# Brightwave CLI Web Crawler

This project implements a single-machine concurrent web crawler with back pressure, persistent storage, and live search during indexing as part of the Brightwave "Build Google in an Afternoon" assignment.

The system includes a crawler (indexer), parser, storage layer, inverted index, search engine, raw storage export, and a local HTTP search API with relevance scoring.

---

## Overview

This project implements a simplified search engine pipeline including:

- Web crawler (indexer)
- HTML parser
- SQLite storage layer
- Inverted index
- Search engine
- Raw storage export files
- Local HTTP search API
- CLI interface
- Persistence and resume functionality

The crawler recursively visits web pages starting from an origin URL, extracts text and links, indexes the content, and allows users to perform search queries while indexing is still ongoing.

All indexed data is stored in a local SQLite database so the system can resume after interruption without losing previously crawled data.

---

## Features

* Crawl from an origin URL up to a maximum depth
* Never visit the same page twice (duplicate prevention)
* Extract links and text content from HTML pages
* Search indexed content while crawling is still running
* Bounded queue for back pressure
* Multi-threaded crawler workers
* SQLite database for persistent storage
* Raw storage export files (`data/storage/*.data`)
* Local search API with relevance scoring
* Persistence and resume after program restart
* CLI commands for indexing, searching, and status tracking
* System status monitoring (queue size, indexed pages, worker status)

---

## Project Structure

```text
crawler-project/
├── core/
│   ├── parser.py
│   ├── storage.py
│   ├── crawler.py
│   └── search.py
├── cli/
│   └── commands.py
├── app/
│   └── main.py          # HTTP search API
├── data/
│   ├── crawler.db       # SQLite database
│   └── storage/
│       ├── a.data
│       ├── b.data
│       ├── p.data
│       └── ...
├── main.py              # CLI entry point
├── requirements.txt
├── README.md
├── product_prd.md
└── recommendation.md
````

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the crawler CLI

```bash
python main.py
```

---

## CLI Commands

```text
index <url> <depth>     Start indexing from a seed URL
search <query>          Search indexed pages
status                  Show current system state
clear                   Clear saved database state
help                    Show help
exit                    Save and quit
```

---

## Example Usage

```text
> index https://example.com 1
> status
> search example
```

Example search result format:

```text
(relevant_url, origin_url, depth)
```

---

## Raw Storage Files

After crawling, indexed words are written into files under:

```text
data/storage/
```

Each line in a storage file has the format:

```text
word relevant_url origin_url depth frequency
```

Example:

```text
python https://www.python.org https://www.python.org 0 5
```

These files are used by the HTTP search API and allow manual inspection of indexed data.

---

## Search API

After crawling some data, start the API server:

```bash
python -m app.main
```

Then open in browser:

```text
http://localhost:3600/search?query=python&sortBy=relevance
```

Example API response fields:

```json
{
  "word": "python",
  "relevant_url": "...",
  "origin_url": "...",
  "depth": 1,
  "frequency": 3,
  "relevance_score": 1025
}
```

Relevance score formula:

```text
score = (frequency × 10) + 1000 − (depth × 5)
```

---

## Persistence and Resume

The crawler uses a local SQLite database to persist indexed pages, visited URLs, word frequencies, and metadata.

This allows the system to resume after interruption without restarting the crawl from scratch. If the program is stopped and started again, previously indexed data remains available for search queries.

---

## Architecture Summary

The system consists of a multi-threaded crawler with a bounded frontier queue, a SQLite storage layer, and an inverted index used by the search engine. Worker threads fetch and parse pages concurrently while the storage layer maintains visited URLs, indexed content, and metadata.

Search queries run on the inverted index and can return results while indexing is still in progress. Indexed data is also exported into raw storage files for transparency and API-based relevance scoring.

Back pressure is implemented using a bounded queue to prevent uncontrolled growth of the crawl frontier. Duplicate URLs are prevented using visited and queued URL tracking sets.

---

## Key Design Decisions

* Used a bounded queue to implement back pressure.
* Implemented an inverted index for fast search.
* Designed a multi-threaded crawler for concurrency.
* Allowed search while indexing is still running.
* Used SQLite database for persistence.
* Exported indexed data into raw storage files.
* Implemented a local HTTP API for relevance-based search.
* Designed modular architecture separating crawler, parser, storage, and search.
* Designed for single-machine execution with persistent storage.

---

## Future Improvements

* Distributed crawling across multiple machines.
* More advanced ranking algorithms (TF-IDF, PageRank).
* Web dashboard instead of CLI.
* Recrawl scheduling and freshness tracking.
* Incremental indexing.
* Caching and performance optimizations.

````

---




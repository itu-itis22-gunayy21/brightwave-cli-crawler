

This project implements a single-machine concurrent web crawler with back pressure and live search during indexing as part of the Brightwave "Build Google in an Afternoon" assignment.

# Brightwave CLI Web Crawler

A single-machine web crawler and live search system built for the “Build Google in an Afternoon” style assignment. The project focuses on clean architecture, concurrency, back pressure, and the ability to search indexed content while crawling is still in progress.



## Overview

This project implements a simplified search engine pipeline including a crawler (indexer), parser, storage layer, inverted index, and search engine. The system runs locally on a single machine and is controlled through a CLI interface.

The crawler recursively visits web pages starting from an origin URL, extracts text and links, indexes the content, and allows users to perform search queries while indexing is still ongoing.



## Features

* Crawl from an origin URL up to a maximum depth
* Never visit the same page twice (duplicate prevention)
* Extract links and text content from HTML pages
* Search indexed content while crawling is still running
* Bounded queue for back pressure
* Multi-threaded crawler workers
* In-memory inverted index for search
* Basic persistence for resume after interruption
* CLI commands for indexing, searching, and status tracking
* System status monitoring (queue size, indexed pages, worker status)



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
├── data/
├── main.py
├── requirements.txt
├── README.md
├── product_prd.md
└── recommendation.md
```

---

## How to Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the crawler CLI:

```bash
python main.py
```

---

## CLI Commands

```text
index <url> <depth>     Start indexing from a seed URL
search <query>          Search indexed pages
status                  Show current system state
clear                   Clear saved state and indexed data
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

## Architecture Summary

The system consists of a multi-threaded crawler with a bounded frontier queue, an in-memory storage layer, and an inverted index used by the search engine. Worker threads fetch and parse pages concurrently while the storage layer maintains visited URLs, indexed content, and metadata. Search queries run on the inverted index and can return results while indexing is still in progress.

Back pressure is implemented using a bounded queue to prevent uncontrolled growth of the crawl frontier. Duplicate URLs are prevented using visited and queued URL tracking sets.

---

## Key Design Decisions

* Used a bounded queue to implement back pressure.
* Implemented an inverted index for fast search.
* Designed a multi-threaded crawler for concurrency.
* Allowed search while indexing is still running.
* Used modular architecture separating crawler, parser, storage, and search.
* Designed for single-machine execution with lightweight persistence.

---

## Future Improvements

* Replace in-memory storage with a database.
* Implement distributed crawling.
* Add more advanced ranking algorithms.
* Add a web-based dashboard instead of CLI.
* Implement recrawl scheduling and freshness tracking.

---


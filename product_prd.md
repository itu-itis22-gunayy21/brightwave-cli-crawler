


# Product Requirement Document

## Brightwave CLI Web Crawler

---

## 1. Overview

The Brightwave CLI Web Crawler is a single-machine web crawling and search system designed to crawl web pages starting from a seed URL, index the content of discovered pages, and allow users to perform searches on indexed content while crawling is still in progress.

The system focuses on concurrency, load management through back pressure, duplicate prevention, and system visibility through a command-line interface. The project demonstrates architectural sensibility, concurrent processing, and basic search engine design principles.

---

## 2. Problem

The goal of this project is to build a web crawler that can recursively crawl web pages from a given origin URL and store indexed content so that users can perform search queries on the crawled pages.

The system must:

* Ensure that pages are not crawled more than once.
* Manage its workload to prevent overload.
* Allow search functionality while indexing is still ongoing.
* Provide visibility into crawler progress and system status.

---

## 3. Goals

The main goals of the system are:

* Crawl web pages recursively up to a specified depth.
* Prevent duplicate page crawling using a visited URL tracking system.
* Provide search functionality over indexed pages.
* Allow search queries while the crawler is still indexing new pages.
* Manage crawler workload using back pressure mechanisms.
* Provide system visibility through a CLI dashboard.
* Support basic persistence so the crawler can resume after interruption.
* Maintain a modular and clean system architecture.

---

## 4. Non-Goals

The following features are intentionally out of scope for this project:

* Distributed crawling across multiple machines.
* JavaScript rendering or dynamic content execution.
* Advanced search ranking algorithms such as PageRank.
* Full production-scale search engine infrastructure.
* Large-scale distributed storage systems.

---

## 5. System Components

### 5.1 Crawler (Indexer)

The crawler is responsible for:

* Fetching web pages from URLs.
* Parsing HTML content.
* Extracting links and text content.
* Adding new URLs to the crawl queue.
* Respecting crawl depth limits.
* Preventing duplicate crawling.
* Updating the search index and metadata storage.

### 5.2 Search Engine

The search engine is responsible for:

* Processing user queries.
* Searching indexed content using an inverted index.
* Ranking results based on keyword frequency and title matches.
* Returning results in the format:

```
(relevant_url, origin_url, depth)
```

Search must work while the crawler is still indexing pages.

### 5.3 CLI Interface

The CLI interface allows users to interact with the system using commands:

```
index <url> <depth>
search <query>
status
clear
help
exit
```

The CLI also provides system visibility such as indexing progress, queue size, and crawler status.

---

## 6. System Architecture

The system follows a modular architecture with the following modules:

* **CLI Module**: Handles user commands and displays system status.
* **Crawler Module**: Manages the crawl queue, worker threads, and crawl logic.
* **Parser Module**: Extracts text and links from HTML pages.
* **Storage Module**: Stores visited URLs, indexed content, and metadata.
* **Search Module**: Handles search queries and ranking.

This modular architecture separates responsibilities and improves maintainability and scalability.

---

## 7. Data Storage

The system uses in-memory data structures for fast indexing and search operations, along with lightweight persistence for crawler state.

The storage layer maintains:

* Visited URLs
* Indexed pages
* Metadata (origin URL and crawl depth)
* Inverted index (word → URLs)
* Frontier queue snapshot for resume functionality

This approach provides fast search performance while still allowing the crawler to resume after interruption.

---

## 8. Data Structures

The system uses the following data structures:

* **Queue**: Stores URLs waiting to be crawled (frontier).
* **Visited Set**: Tracks URLs that have already been crawled.
* **Queued Set**: Tracks URLs already scheduled for crawling.
* **Inverted Index**: Maps words to URLs where they appear.
* **Metadata Store**: Maps each URL to its origin URL and crawl depth.
* **Worker Threads**: Process crawl tasks concurrently.

---

## 9. Concurrency

The crawler uses multiple worker threads to fetch and process pages concurrently. Shared data structures such as the visited set, inverted index, and metadata storage are protected to ensure thread safety and prevent data corruption.

Concurrency allows the system to crawl multiple pages simultaneously and improves crawling performance.

---

## 10. Back Pressure

Back pressure is implemented using a bounded queue. The crawler queue has a maximum capacity, and when the queue is full, newly discovered URLs are not added to the queue.

This prevents uncontrolled memory growth and excessive crawling load and ensures the system remains stable during large crawls.

---

## 11. System Visibility

The system provides visibility through the CLI **status** command. The following metrics are displayed:

* Current indexing progress
* Number of indexed pages
* Queue size
* Worker activity
* Back pressure status
* Success and failure counts

This allows users to monitor crawler behavior in real time.

---

## 12. Result Format

Search results are returned in the following format:

```
(relevant_url, origin_url, depth)
```

Where:

* **relevant_url** is the indexed page matching the query.
* **origin_url** is the seed URL from which the page was discovered.
* **depth** is the crawl depth at which the page was found.

---

## 13. Future Improvements

The system can be extended in the future by:

* Using a database for persistent storage.
* Implementing distributed crawling across multiple machines.
* Adding advanced search ranking algorithms.
* Implementing recrawl scheduling.
* Adding a web-based dashboard instead of CLI.
* Implementing fuzzy search and spell correction.

---

## 14. Notes

* The system is designed to run on a single machine.
* Search works while indexing is still running.
* The system demonstrates concurrency, back pressure, and search indexing.
* The architecture can be extended to a production-scale crawler.

---


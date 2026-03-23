








# Product Requirement Document

## Product Name
Brightwave Web Crawler and Search System

---

## 1. Overview

The Brightwave Web Crawler is a single-machine web crawling and search system designed to crawl web pages starting from a seed URL, index the content of discovered pages, and allow users to perform searches on indexed content while crawling is still in progress.

The system focuses on concurrency, load management through back pressure, duplicate prevention, and system visibility through a command-line interface and a local search API. The project demonstrates architectural sensibility, concurrent processing, indexing, and basic search engine ranking logic.

---

## 2. Problem

The goal of this project is to build a web crawler that can recursively crawl web pages from a given origin URL and store indexed content so that users can perform search queries on the crawled pages.

The system must:

- Ensure that pages are not crawled more than once.
- Manage its workload to prevent overload.
- Allow search functionality while indexing is still ongoing.
- Provide visibility into crawler progress and system status.
- Export indexed data into raw storage files.
- Provide a local API to search indexed data and calculate relevance scores.

---

## 3. Goals

The main goals of the system are:

- Crawl web pages recursively up to a specified depth.
- Prevent duplicate page crawling using a visited URL tracking system.
- Provide search functionality over indexed pages.
- Allow search queries while the crawler is still indexing new pages.
- Manage crawler workload using back pressure mechanisms.
- Provide system visibility through a CLI dashboard.
- Export indexed words into raw storage files.
- Provide a local HTTP search API.
- Calculate relevance scores for search results.
- Support basic persistence so the crawler can resume after interruption.
- Maintain a modular and clean system architecture.

---

## 4. Non-Goals

The following features are intentionally out of scope for this project:

- Distributed crawling across multiple machines.
- JavaScript rendering or dynamic content execution.
- Advanced search ranking algorithms such as PageRank.
- Full production-scale search engine infrastructure.
- Large-scale distributed storage systems.

---

## 5. System Components

### 5.1 Crawler (Indexer)

The crawler is responsible for:

- Fetching web pages from URLs.
- Parsing HTML content.
- Extracting links and text content.
- Adding new URLs to the crawl queue.
- Respecting crawl depth limits.
- Preventing duplicate crawling.
- Updating the search index and metadata storage.
- Exporting indexed words into storage files.

---

### 5.2 Search Engine

The search engine is responsible for:

- Processing user queries.
- Searching indexed content using an inverted index.
- Ranking results based on keyword frequency and depth.
- Returning results in the format:

```

(relevant_url, origin_url, depth)

```

Search must work while the crawler is still indexing pages.

---

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

### 5.4 Search API

The system also exposes a local HTTP API that allows searching indexed data.

Example endpoint:

```

GET [http://localhost:3600/search?query=python&sortBy=relevance](http://localhost:3600/search?query=python&sortBy=relevance)

```

The API returns search results including relevance scores.

---

## 6. System Architecture

The system follows a modular architecture with the following modules:

- **CLI Module**: Handles user commands and displays system status.
- **Crawler Module**: Manages the crawl queue, worker threads, and crawl logic.
- **Parser Module**: Extracts text and links from HTML pages.
- **Storage Module**: Stores visited URLs, indexed content, metadata, and raw storage files.
- **Search Module**: Handles search queries and ranking.
- **API Module**: Provides HTTP search interface and relevance scoring.

This modular architecture separates responsibilities and improves maintainability and scalability.

---

## 7. Data Storage

The system uses a hybrid storage approach:

### In-Memory Storage
Used for fast indexing and search operations:
- Visited URLs
- Indexed pages
- Inverted index
- Metadata
- Crawl queue snapshot

### Raw Storage Files
Indexed words are exported into files located in:

```

data/storage/

```

Each line in the storage files follows the format:

```

word relevant_url origin_url depth frequency

```

These files allow manual inspection of indexed data and are used by the search API.

---

## 8. Data Structures

The system uses the following data structures:

- **Queue**: Stores URLs waiting to be crawled (frontier).
- **Visited Set**: Tracks URLs that have already been crawled.
- **Queued Set**: Tracks URLs already scheduled for crawling.
- **Inverted Index**: Maps words to URLs where they appear.
- **Metadata Store**: Maps each URL to its origin URL and crawl depth.
- **Worker Threads**: Process crawl tasks concurrently.
- **Raw Storage Files**: Store indexed word entries for API search.

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

- Current indexing progress
- Number of indexed pages
- Queue size
- Worker activity
- Back pressure status
- Success and failure counts

This allows users to monitor crawler behavior in real time.

---

## 12. Relevance Scoring

Search results returned by the API include a relevance score calculated using the following formula:

```

score = (frequency × 10) + 1000 − (depth × 5)

```

Where:
- **frequency** is how many times the word appears on the page.
- **depth** is the crawl depth where the page was found.
- Exact word matches receive a bonus score.

This scoring system prioritizes pages where the word appears frequently and pages closer to the origin URL.

---

## 13. Result Format

Search results are returned in the following format:

```

(relevant_url, origin_url, depth)

```

API results also include:
- frequency
- relevance_score

---

## 14. Future Improvements

The system can be extended in the future by:

- Using a database for persistent storage.
- Implementing distributed crawling across multiple machines.
- Adding advanced search ranking algorithms.
- Implementing recrawl scheduling.
- Adding a web-based dashboard instead of CLI.
- Implementing fuzzy search and spell correction.
- Adding caching and incremental indexing.

---

## 15. Notes

- The system is designed to run on a single machine.
- Search works while indexing is still running.
- The system demonstrates concurrency, back pressure, and search indexing.
- Raw storage files allow verification of indexed data.
- The architecture can be extended to a production-scale crawler.
```

---


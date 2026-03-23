import os
import re
from collections import defaultdict
from flask import Flask, jsonify, request

app = Flask(__name__)

STORAGE_DIR = "data/storage"
WORD_RE = re.compile(r"\b[a-zA-Z]{2,}\b")


def normalize_query(query: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(query)]


def storage_file_for_word(word: str) -> str:
    first = word[0].lower() if word else "other"
    if not first.isalpha():
        first = "other"
    return os.path.join(STORAGE_DIR, f"{first}.data")


def calculate_relevance_score(frequency: int, depth: int, exact_match: bool = True) -> int:
    score = (frequency * 10) - (depth * 5)
    if exact_match:
        score += 1000
    return score


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "").strip()
    sort_by = request.args.get("sortBy", "relevance")
    page_limit = request.args.get("pageLimit", default=10, type=int)
    page_offset = request.args.get("pageOffset", default=0, type=int)

    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    query_words = normalize_query(query)
    if not query_words:
        return jsonify({"error": "No valid search terms found"}), 400

    results_by_url = {}

    for word in query_words:
        filename = storage_file_for_word(word)
        if not os.path.exists(filename):
            continue

        with open(filename, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue

                parts = line.split(" ", 4)
                if len(parts) != 5:
                    continue

                stored_word, relevant_url, origin_url, depth_str, frequency_str = parts

                if stored_word != word:
                    continue

                try:
                    depth = int(depth_str)
                    frequency = int(frequency_str)
                except ValueError:
                    continue

                relevance_score = calculate_relevance_score(frequency, depth, exact_match=True)

                entry = {
                    "word": stored_word,
                    "relevant_url": relevant_url,
                    "origin_url": origin_url,
                    "depth": depth,
                    "frequency": frequency,
                    "relevance_score": relevance_score,
                }

                if relevant_url not in results_by_url:
                    results_by_url[relevant_url] = entry
                else:
                    if entry["relevance_score"] > results_by_url[relevant_url]["relevance_score"]:
                        results_by_url[relevant_url] = entry

    results = list(results_by_url.values())

    if sort_by == "frequency":
        results.sort(key=lambda x: (-x["frequency"], x["depth"], x["relevant_url"]))
    elif sort_by == "depth":
        results.sort(key=lambda x: (x["depth"], -x["relevance_score"], x["relevant_url"]))
    else:
        results.sort(key=lambda x: (-x["relevance_score"], x["depth"], x["relevant_url"]))

    paginated = results[page_offset:page_offset + page_limit]

    return jsonify(
        {
            "query": query,
            "results": paginated,
            "total_results": len(results),
            "sort_by": sort_by,
            "query_words": query_words,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3600, debug=True)
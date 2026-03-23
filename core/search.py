from core.parser import tokenize
from core.storage import Storage


class SearchEngine:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def search(self, query: str) -> list[tuple[str, str, int]]:
        terms = tokenize(query)
        if not terms:
            return []

        ranked = self.storage.search(terms)
        results: list[tuple[str, str, int]] = []

        for url, _score in ranked:
            metadata = self.storage.get_result_metadata(url)
            if metadata is None:
                continue

            origin_url, depth = metadata
            results.append((url, origin_url, depth))

        return results
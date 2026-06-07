"""Search engine implementation sample."""

from __future__ import annotations

class SearchEngine:
    """Implement a new search engine for manual classifier validation."""

    def __init__(self) -> None:
        self._documents: dict[str, str] = {}

    def add_document(self, key: str, text: str) -> None:
        """Create a searchable document entry."""
        self._documents[key] = text

    def search(self, query: str) -> list[str]:
        """Support simple substring search over indexed documents."""
        return [key for key, text in self._documents.items() if query in text]

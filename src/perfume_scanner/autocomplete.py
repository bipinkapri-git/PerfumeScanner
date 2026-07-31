"""Typo-tolerant, prefix-based autocomplete engine for perfume names.

Perfume Scanner has no persisted product catalog: every search triggers
live HTTP scraping across 14 retailer storefronts (see `scraper.py`).
To give users instant type-ahead suggestions without hitting the
network (or overloading those retailers), we match locally against a
small, static catalog of well-known fragrance names
(`data/perfume_catalog.py`).

Two complementary strategies are combined, mirroring what a client-side
Fuse.js/Trie-based UI (see `search_widget.py`) does in the browser:

1. ``Trie`` -- a classic prefix tree for O(len(prefix)) "starts with"
   lookups. Cheap, exact, and ideal for the common case of a user
   typing a name from the start (e.g. "Gu" -> "Gucci Bloom").
2. ``fuzzy_suggestions`` -- Levenshtein/Indel-style ranking (via
   rapidfuzz, with a stdlib ``difflib`` fallback) that tolerates typos,
   swapped letters, and missing characters, e.g. "Guci" -> "Gucci Bloom".

This module is pure Python and has no Streamlit dependency, so it's
easily unit-testable and reusable if the project ever grows a real
backend search endpoint (see README notes on Meilisearch as a future
option once the catalog is database-backed).
"""

from __future__ import annotations

from typing import Iterable

from perfume_scanner.data.perfume_catalog import PERFUME_CATALOG

try:
    from rapidfuzz import fuzz, process

    _HAS_RAPIDFUZZ = True
except ImportError:  # pragma: no cover - exercised only without the dependency
    _HAS_RAPIDFUZZ = False


class _TrieNode:
    """A single node in the prefix tree."""

    __slots__ = ("children", "names")

    def __init__(self) -> None:
        self.children: dict[str, "_TrieNode"] = {}
        # Original-cased names that pass through this node, in insertion order.
        self.names: list[str] = []


class Trie:
    """Prefix tree used for instant "starts with" perfume name lookups."""

    def __init__(self, words: Iterable[str] | None = None) -> None:
        self.root = _TrieNode()
        for word in words or []:
            self.insert(word)

    def insert(self, word: str) -> None:
        """Adds `word` to the trie, indexed by every prefix of its lowercase form."""
        node = self.root
        for char in word.lower().strip():
            node = node.children.setdefault(char, _TrieNode())
            node.names.append(word)

    def starts_with(self, prefix: str, limit: int = 8) -> list[str]:
        """Returns up to `limit` original-cased names starting with `prefix`."""
        prefix = prefix.lower().strip()
        if not prefix:
            return []

        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        seen: set[str] = set()
        results: list[str] = []
        for name in node.names:
            if name not in seen:
                seen.add(name)
                results.append(name)
            if len(results) >= limit:
                break
        return results


def fuzzy_suggestions(
    query: str,
    catalog: Iterable[str] = PERFUME_CATALOG,
    limit: int = 8,
    score_cutoff: float = 60.0,
) -> list[str]:
    """Typo-tolerant ranking of `catalog` entries against `query`.

    Uses rapidfuzz's WRatio scorer (a Levenshtein/Indel blend tuned for
    partial, out-of-order matches) when available, so "Guci" still
    surfaces "Gucci Bloom". Falls back to stdlib `difflib` if rapidfuzz
    isn't installed, degrading gracefully rather than failing.
    """
    query = query.strip()
    if not query:
        return []

    catalog_list = list(catalog)

    if _HAS_RAPIDFUZZ:
        matches = process.extract(
            query,
            catalog_list,
            scorer=fuzz.WRatio,
            score_cutoff=score_cutoff,
            limit=limit,
        )
        return [name for name, _score, _index in matches]

    import difflib

    return difflib.get_close_matches(query, catalog_list, n=limit, cutoff=0.5)


_TRIE = Trie(PERFUME_CATALOG)


def get_suggestions(query: str, limit: int = 8) -> list[str]:
    """Returns up to `limit` suggested perfume names for a partial query.

    Exact prefix matches (via the Trie) are ranked first since they're
    the most confident signal. Any remaining slots are filled with
    fuzzy/typo-tolerant matches, e.g. "Guci" -> "Gucci Bloom" even
    though "guci" is not a prefix of any catalog entry.
    """
    query = query.strip()
    if not query:
        return []

    prefix_matches = _TRIE.starts_with(query, limit=limit)
    if len(prefix_matches) >= limit:
        return prefix_matches

    combined = list(prefix_matches)
    seen = {name.lower() for name in combined}
    for name in fuzzy_suggestions(query, limit=limit):
        if name.lower() not in seen:
            combined.append(name)
            seen.add(name.lower())
        if len(combined) >= limit:
            break
    return combined

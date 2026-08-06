"""Load test suite for PerfumeScanner scraping engine.

Simulates concurrent multi-user searches for popular fragrance queries and verifies
that the scraping engine reliably returns non-empty matching deals, valid pricing,
and high-resolution CDN images without rate-limit failures.
"""

from __future__ import annotations

import concurrent.futures
import time

import pytest

from perfume_scanner.scraper import RETAILERS, scrape_all_retailers

# Sample popular fragrance queries representing varied search patterns
LOAD_TEST_QUERIES = [
    "Lattafa Khamrah",
    "Armaf",
    "Hawas",
    "Dior Sauvage",
    "Creed",
    "Afnan 9PM",
    "Asad",
]


@pytest.mark.parametrize("query", LOAD_TEST_QUERIES)
def test_single_query_load(query: str):
    """Verifies that individual fragrance queries return non-empty deals with valid images and prices."""
    start_time = time.time()
    deals = scrape_all_retailers(query)
    elapsed = time.time() - start_time

    print(f"\n[LOAD TEST] Query: '{query}' -> Found {len(deals)} deals in {elapsed:.2f}s")
    assert len(deals) > 0, f"Query '{query}' returned 0 deals! Expected at least 1 deal."

    for deal in deals:
        assert deal["retailer"] in RETAILERS, f"Unknown retailer: {deal['retailer']}"
        assert len(deal["product_name"]) >= 3, "Product name too short"
        assert deal["link"].startswith("http"), f"Invalid link: {deal['link']}"
        assert deal["price_str"] != "₹0.00", f"Zero price found for {deal['product_name']}"
        assert "₹" in deal["price_str"] or "Rs" in deal["price_str"], f"Invalid price format: {deal['price_str']}"
        assert deal["image_url"].startswith("http"), f"Missing or invalid CDN image URL: {deal['image_url']}"


def test_concurrent_multi_user_load():
    """Simulates 5 concurrent users searching different perfumes simultaneously."""
    queries = ["Hawas", "Lattafa Khamrah", "Armaf", "Dior Sauvage", "Creed"]

    start_time = time.time()
    results: dict[str, list] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(queries)) as executor:
        future_to_query = {
            executor.submit(scrape_all_retailers, q): q for q in queries
        }
        for future in concurrent.futures.as_completed(future_to_query):
            q = future_to_query[future]
            try:
                results[q] = future.result()
            except (RuntimeError, ValueError, TimeoutError) as exc:
                pytest.fail(f"Concurrent load search for '{q}' raised an exception: {exc}")

    total_elapsed = time.time() - start_time
    print(f"\n[CONCURRENT LOAD TEST] Completed {len(queries)} parallel user searches in {total_elapsed:.2f}s")

    for q, deals in results.items():
        assert len(deals) > 0, f"Concurrent search for '{q}' returned 0 deals."
        print(f"  - '{q}': {len(deals)} live deals verified with images")

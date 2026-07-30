"""Scraper engine for Perfume Scanner.

Queries 11 Indian perfume platforms concurrently in parallel for maximum speed.
Only displays retailers where the searched product is genuinely found and matches
the search query keywords.
"""

from __future__ import annotations

import concurrent.futures
import re
import urllib.parse
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# Realistic headers to bypass bot blocks
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

# Shared Session with connection pooling for performance optimization
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=20, pool_maxsize=30, max_retries=1
)
session.mount("https://", adapter)
session.mount("http://", adapter)

# The 14 Indian retailers requested by the user
RETAILERS = {
    "Sillage Perfumes": {
        "base_url": "https://sillageperfumes.in",
        "search_url": "https://sillageperfumes.in/search?q={query}",
        "is_shopify": True,
    },
    "All Arabic": {
        "base_url": "https://allarabic.in",
        "search_url": "https://allarabic.in/search?q={query}",
        "is_shopify": True,
    },
    "Ahmed Al Maghribi India": {
        "base_url": "https://ahmedalmaghribi.co.in",
        "search_url": "https://ahmedalmaghribi.co.in/search?q={query}",
        "is_shopify": True,
    },
    "FridayCharm": {
        "base_url": "https://fridaycharm.com",
        "search_url": "https://fridaycharm.com/search?q={query}",
        "is_shopify": True,
    },
    "Belvish": {
        "base_url": "https://belvish.com",
        "search_url": "https://belvish.com/search?q={query}",
        "is_shopify": True,
    },
    "Perfume Palace": {
        "base_url": "https://perfumepalace.in",
        "search_url": "https://perfumepalace.in/search?q={query}",
        "is_shopify": True,
    },
    "Naseem Perfume India": {
        "base_url": "https://naseemperfume.in",
        "search_url": "https://naseemperfume.in/search?q={query}",
        "is_shopify": True,
    },
    "Splash Fragrance": {
        "base_url": "https://splashfragrance.in",
        "search_url": "https://splashfragrance.in/search?q={query}",
        "is_shopify": True,
    },
    "Scentira": {
        "base_url": "https://scentira.in",
        "search_url": "https://scentira.in/search?q={query}",
        "is_shopify": True,
    },
    "Perfume Network India": {
        "base_url": "https://perfumenetwork.in",
        "search_url": "https://perfumenetwork.in/search?q={query}",
        "is_shopify": True,
    },
    "Parcos": {
        "base_url": "https://www.parcos.com",
        "search_url": "https://www.parcos.com/search?q={query}",
        "is_shopify": False,
    },
    "Nykaa / Nykaa Man": {
        "base_url": "https://www.nykaa.com",
        "search_url": "https://www.nykaa.com/search/result/?q={query}",
        "is_shopify": False,
    },
    "Tata CLiQ Luxury": {
        "base_url": "https://luxury.tatacliq.com",
        "search_url": "https://luxury.tatacliq.com/search/?text={query}",
        "is_shopify": False,
    },
    "Skinn by Titan": {
        "base_url": "https://www.skinn.in",
        "search_url": "https://www.skinn.in/search?q={query}",
        "is_shopify": True,
    },
}


def is_matching_product(query: str, product_title: str) -> bool:
    """Verifies if the scraped product title matches the searched query keywords.

    At least 75% of non-generic search query words must be present in the title
    (case-insensitive) to ensure exact matches.
    """
    if not query or not product_title:
        return False

    query_lower = query.lower()
    product_title_lower = product_title.lower()

    # Exclude decants, samples, vials, splits unless specifically searched
    decant_words = [
        "decant",
        "sample",
        "vial",
        "split",
        "2ml",
        "5ml",
        "8ml",
        "10ml",
        "12ml",
        "5 ml",
        "10 ml",
    ]
    user_searching_decant = any(
        dw in query_lower for dw in ["decant", "sample", "vial", "split"]
    )
    if not user_searching_decant:
        for word in decant_words:
            if word in product_title_lower and word not in query_lower:
                return False

    # Also exclude clones, alternatives, impressions, inspired by unless specifically searched
    clone_words = ["inspired by", "impression", "clone", "alternative", "inspired-by"]
    user_searching_clone = any(
        cw in query_lower for cw in ["clone", "impression", "inspired", "alternative"]
    )
    if not user_searching_clone:
        for word in clone_words:
            if word in product_title_lower and word not in query_lower:
                return False

    # Standard stop words to exclude from strict keyword matching
    stop_words = {
        "for",
        "men",
        "women",
        "unisex",
        "perfume",
        "edp",
        "edt",
        "cologne",
        "spray",
        "ml",
        "oz",
        "and",
        "de",
        "parfum",
        "toilette",
    }

    # Split query into words
    query_words = re.findall(r"\w+", query.lower())
    # Filter out stop words
    keywords = [w for w in query_words if w not in stop_words and len(w) > 1]

    if not keywords:
        keywords = [w for w in query_words if len(w) > 1]

    if not keywords:
        return True  # Fallback for empty keyword lists

    # Count matching keywords
    match_count = sum(1 for kw in keywords if kw in product_title_lower)

    # Require all keywords if 1 or 2 keywords, else require at least 75%
    if len(keywords) <= 2:
        return match_count == len(keywords)
    else:
        return match_count >= (len(keywords) * 0.75)


def resize_shopify_image(url: str, width: int = 300) -> str:
    """Modifies Shopify CDN image URLs to request smaller, optimized resolutions."""
    if not url:
        return ""
    # Replace {width} template variables commonly used in lazy-loaded images
    if "{width}" in url:
        url = url.replace("{width}", str(width))
    if "cdn.shopify.com" in url or any(
        domain in url
        for domain in [
            "sillageperfumes.in",
            "allarabic.in",
            "fridaycharm.com",
            "belvish.com",
            "perfumepalace.in",
            "naseemperfume.in",
            "splashfragrance.in",
            "scentira.in",
            "perfumenetwork.in",
            "skinn.in",
        ]
    ):
        # Replace image size suffixes in the filename like _150x or _300x with our target width
        url = re.sub(r"_\d+x\.", f"_{width}x.", url)
        # Replace existing width parameters
        url = re.sub(r"width=\d+", f"width={width}", url)
        if "width=" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}width={width}"
    return url


def scrape_retailer(retailer_name: str, query: str) -> dict[str, Any] | None:
    """Scrapes search results from a store and returns the first matching product.

    Returns None if no matching products are found or if the request fails.
    """
    config = RETAILERS[retailer_name]
    query_encoded = urllib.parse.quote_plus(query)
    search_url = config["search_url"].format(query=query_encoded)

    # Currently we only scrape Shopify stores in this client
    if not config["is_shopify"]:
        return None

    try:
        response = session.get(search_url, headers=BROWSER_HEADERS, timeout=3.5)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all product links
        product_links = soup.find_all("a", href=re.compile(r"/products/"))

        seen_links = set()

        for link in product_links:
            href = link.get("href", "")
            prod_url = f"{config['base_url']}{href}" if href.startswith("/") else href

            clean_url = prod_url.split("?")[0]
            if clean_url in seen_links:
                continue

            # Traverse up to find the closest ancestor containing BOTH a price and an image (full product card wrapper)
            parent = link.parent
            card_container = None
            for _ in range(6):
                if parent is None:
                    break
                has_price = parent.find(
                    class_=re.compile(r"price|money|sale-price")
                ) or parent.find(string=re.compile(r"Rs\.|\bRs\b|₹"))
                has_image = parent.find("img") or parent.find(
                    attrs={"data-bgset": True}
                )
                if has_price and has_image:
                    card_container = parent
                    break
                parent = parent.parent

            if not card_container:
                continue

            # Verify that the card container only contains links to this specific product (avoid broad parent body containers)
            prod_links = card_container.find_all("a", href=re.compile(r"/products/"))
            prod_paths = set()
            for link_el in prod_links:
                href_attr = link_el.get("href", "")
                if href_attr:
                    path = href_attr.split("?")[0].split("#")[0]
                    if path.startswith("/"):
                        path = f"{config['base_url']}{path}"
                    prod_paths.add(path)

            if len(prod_paths) > 1:
                continue

            # Skip sold out or out of stock items
            is_sold_out = False

            variant_script = card_container.find("script", type="application/json")
            if variant_script:
                try:
                    import json

                    variants = json.loads(variant_script.string)
                    if isinstance(variants, list) and len(variants) > 0:
                        is_sold_out = not any(
                            v.get("available", False) for v in variants
                        )
                    elif isinstance(variants, dict):
                        is_sold_out = not variants.get("available", True)
                except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
                    pass
            else:
                sold_out_badge = card_container.find(
                    class_=re.compile(
                        r"badge|label|btn|button|sold-out|out-of-stock", re.IGNORECASE
                    ),
                    string=re.compile(
                        r"sold\s*out|out\s*of\s*stock|unavailable", re.IGNORECASE
                    ),
                )
                if sold_out_badge:
                    is_sold_out = True

            if is_sold_out:
                continue

            # Remove script and style tags to prevent code/CSS from polluting text
            for code_el in card_container.find_all(["script", "style"]):
                code_el.decompose()

            # Decompose rating, review, star, and review-badge elements so review scores (e.g. 4.79113924) are not misparsed as prices
            for rating_el in card_container.find_all(
                class_=re.compile(
                    r"rating|review|jdgm|stamped|yotpo|loox|spr-badge|star|score",
                    re.IGNORECASE,
                )
            ):
                rating_el.decompose()
            for rating_attr in (
                card_container.find_all(attrs={"data-rating": True})
                + card_container.find_all(attrs={"data-score": True})
                + card_container.find_all(attrs={"data-average-rating": True})
            ):
                rating_attr.decompose()
            for hidden_rating in card_container.find_all(attrs={"aria-hidden": "true"}):
                txt = hidden_rating.get_text(strip=True)
                if "/" in txt or "out of" in txt.lower() or "stars" in txt.lower():
                    hidden_rating.decompose()

            # Title extraction
            title = ""
            link_text = " ".join(link.get_text(strip=True).split())
            if (
                link_text
                and len(link_text) >= 5
                and "rs." not in link_text.lower()
                and "₹" not in link_text.lower()
            ):
                title = link_text

            if not title:
                title_el = card_container.find(
                    class_=re.compile(r"title|name|heading|card__heading")
                )
                if title_el:
                    title = title_el.get_text(strip=True)
            if not title:
                title = link.get_text(strip=True)

            title = " ".join(title.split())

            # Skip invalid titles or titles containing pricing info
            if (
                not title
                or len(title) < 5
                or "rs." in title.lower()
                or "₹" in title.lower()
            ):
                continue

            # Strict Description Verification: Check if product title matches search query
            if not is_matching_product(query, title):
                continue

            # Remove crossed-out/compare-at prices to prevent showing regular price
            for strike_el in card_container.find_all(["s", "del", "strike"]):
                strike_el.decompose()
            for compare_el in card_container.find_all(
                class_=re.compile(r"compare|old|original|was-price", re.IGNORECASE)
            ):
                compare_el.decompose()
            for save_el in card_container.find_all(
                class_=re.compile(r"save|saving|discount", re.IGNORECASE)
            ):
                save_el.decompose()
            for hidden_el in card_container.find_all(
                class_=re.compile(r"visually-hidden|sr-only", re.IGNORECASE)
            ):
                hidden_el.decompose()

            # Price extraction
            price_str = ""
            price_elements = card_container.find_all(
                class_=re.compile(r"price|money|sale-price")
            )
            # Combine all text from all price elements to make sure we capture both regular and sale prices
            if price_elements:
                price_str = " ".join(
                    [
                        el.get_text(strip=True)
                        for el in price_elements
                        if el.get_text(strip=True)
                    ]
                )

            if not price_str:
                price_text_el = card_container.find(string=re.compile(r"Rs\.|\bRs\b|₹"))
                if price_text_el:
                    price_str = price_text_el.parent.get_text(strip=True)

            price_str = " ".join(price_str.split())

            # Remove saving text patterns like "Save Rs. X" or "Save Z%" from the price string
            if price_str:
                saving_pattern = r"(?:you\s+)?save?s?\s*(?::)?\s*(?:Rs\.?|₹)?\s*\d+(?:,\d+)*(?:\.\d+)?"
                price_str = re.sub(saving_pattern, "", price_str, flags=re.IGNORECASE)

            # Extract currency numbers and find the active/lowest price
            if price_str:
                price_matches = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", price_str)
                # Filter out percentage values and numbers outside valid perfume price bounds (e.g. ratings < 50)
                filtered_matches = []
                for m in price_matches:
                    match_esc = re.escape(m)
                    if re.search(match_esc + r"\s*%", price_str):
                        continue
                    try:
                        num = float(m.replace(",", ""))
                        if 50.0 <= num <= 1000000.0:  # Valid price in INR
                            filtered_matches.append((num, m))
                    except (ValueError, TypeError):
                        pass

                if filtered_matches:
                    # Sort to find the lowest active sale price
                    filtered_matches.sort(key=lambda x: x[0])
                    _lowest_num, lowest_str = filtered_matches[0]
                    symbol = "Rs. " if "rs" in price_str.lower() else "₹"
                    price_str = f"{symbol}{lowest_str}"
                else:
                    price_str = ""

            # Image URL extraction
            image_url = ""

            # Try lazyloaded background images (data-bgset) first
            bg_el = card_container.find(attrs={"data-bgset": True})
            if bg_el:
                bg_set = bg_el.get("data-bgset", "")
                urls = [u.strip().split(" ")[0] for u in bg_set.split(",") if u.strip()]
                if urls:
                    image_url = urls[0]

            if not image_url:
                imgs = card_container.find_all("img")
                for img_el in imgs:
                    # Prioritize lazy-loaded data-src/srcset attributes
                    src = (
                        img_el.get("data-src")
                        or img_el.get("data-srcset")
                        or img_el.get("srcset")
                        or img_el.get("data-lazy")
                        or img_el.get("src")
                        or ""
                    )

                    # If the chosen attribute was empty or was a data: image placeholder, check other attributes
                    if not src or src.startswith("data:"):
                        # Fallback to src if it's not a data URL
                        raw_src = img_el.get("src") or ""
                        if raw_src and not raw_src.startswith("data:"):
                            src = raw_src
                        else:
                            continue

                    if "," in src:
                        src = src.split(",")[0].strip().split(" ")[0]

                    if not src or any(
                        k in src.lower()
                        for k in [
                            "logo",
                            "icon",
                            "badge",
                            "payment",
                            "pixel",
                            "noscript",
                            "/tr",
                            "gif",
                        ]
                    ):
                        continue

                    image_url = src
                    break

            if image_url:
                # Fix protocol
                if image_url.startswith("//"):
                    image_url = f"https:{image_url}"
                elif not image_url.startswith("http"):
                    image_url = f"{config['base_url']}{image_url}"

                # Resize and replace placeholders like {width}
                image_url = resize_shopify_image(image_url, 300)

            if title and price_str:
                seen_links.add(clean_url)
                return {
                    "retailer": retailer_name,
                    "product_name": title,
                    "price_str": price_str,
                    "link": clean_url,
                    "image_url": image_url,
                    "is_simulated": False,
                }

    except (requests.RequestException, KeyError, ValueError, TypeError):
        pass

    return None


def scrape_all_retailers(
    query: str, selected_retailers: list[str] | None = None
) -> list[dict[str, Any]]:
    """Runs scraping across selected Indian retailers concurrently in parallel."""
    if not query or not query.strip():
        return []

    if not selected_retailers:
        selected_retailers = list(RETAILERS.keys())

    results = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(selected_retailers)
    ) as executor:
        future_to_retailer = {
            executor.submit(scrape_retailer, retailer, query): retailer
            for retailer in selected_retailers
        }

        for future in concurrent.futures.as_completed(future_to_retailer):
            try:
                deal = future.result()
                if (
                    deal
                ):  # Only append stores that successfully returned a matching deal
                    results.append(deal)
            except (
                requests.RequestException,
                KeyError,
                ValueError,
                TypeError,
                concurrent.futures.CancelledError,
            ):
                pass

    return results

"""Scraper engine for Perfume Scanner.

This module searches 5 popular perfume retailers:
1. FragranceNet
2. FragranceX
3. Perfume.com
4. Jomashop
5. MaxAroma

Due to Cloudflare / bot protection on e-commerce sites, the scraper attempts
a real HTTP query with realistic headers, and automatically falls back to a
stable, deterministic simulated search result if blocked or timed out.
"""

import hashlib
import urllib.parse
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup

# Standard user headers to resemble a real browser
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

RETAILERS = {
    "FragranceNet": {
        "search_url": "https://www.fragrancenet.com/search?f=f1!us&s={query}",
        "base_url": "https://www.fragrancenet.com",
        "selectors": {
            "item": "div.matrix-item, div.product-card",
            "title": "span.title, div.product-title, h3.title",
            "price": "span.price, div.product-price, .price",
            "link": "a.lnk-product, a.product-link"
        },
        "price_multiplier": 0.92,
        "product_template": "{query} Eau De Parfum Spray 3.4 oz",
        "dummy_path": "/perfume/search?s={query_slug}"
    },
    "FragranceX": {
        "search_url": "https://www.fragrancex.com/search/search_results?query={query}",
        "base_url": "https://www.fragrancex.com",
        "selectors": {
            "item": "div.product-grid-item, div.product-card, div.grid-item",
            "title": "h3.product-name, div.title, .product-title",
            "price": "span.price, div.price, .product-price",
            "link": "a.product-link, a.link"
        },
        "price_multiplier": 0.95,
        "product_template": "{query} Perfume, 3.4 oz EDP Spray",
        "dummy_path": "/products/search?query={query_slug}"
    },
    "Perfume.com": {
        "search_url": "https://www.perfume.com/search/search_results?query={query}",
        "base_url": "https://www.perfume.com",
        "selectors": {
            "item": "div.product-card, div.grid-item, div.item",
            "title": "h3.title, div.product-name, .name",
            "price": "div.price, span.price, .product-price",
            "link": "a.product-link, a"
        },
        "price_multiplier": 1.05,
        "product_template": "{query} EDP Spray (tester) 3.4 oz",
        "dummy_path": "/search?query={query_slug}"
    },
    "Jomashop": {
        "search_url": "https://www.jomashop.com/search?q={query}",
        "base_url": "https://www.jomashop.com",
        "selectors": {
            "item": "div.productItem, div.product-card, li.product-item",
            "title": "span.name, h3.title, div.title",
            "price": "div.price, span.price, .price-box",
            "link": "a.product-link, a"
        },
        "price_multiplier": 0.89,
        "product_template": "{query} Eau De Parfum 100ml",
        "dummy_path": "/{query_slug}-edt-100ml"
    },
    "MaxAroma": {
        "search_url": "https://www.maxaroma.com/search?q={query}",
        "base_url": "https://www.maxaroma.com",
        "selectors": {
            "item": "div.product-item, div.product-card, .item-box",
            "title": "div.name, h3.title, a.title",
            "price": "span.price, div.price, .regular-price",
            "link": "a.product-image, a.link"
        },
        "price_multiplier": 1.10,
        "product_template": "{query} Spray for Unisex 3.4 oz",
        "dummy_path": "/search/{query_slug}"
    }
}


def generate_deterministic_simulated_deal(retailer_name: str, query: str) -> Dict[str, Any]:
    """Generates a stable, realistic product pricing for a retailer.
    
    This ensures that when real web scraping gets blocked (e.g. status code 403 / Cloudflare),
    the application still renders mock pricing that is deterministic and consistent.
    """
    config = RETAILERS[retailer_name]
    clean_query = query.strip().title()
    query_slug = urllib.parse.quote_plus(clean_query.lower())

    # Generate a deterministic base price based on query string hash
    hash_obj = hashlib.sha256(clean_query.encode("utf-8"))
    hex_digest = hash_obj.hexdigest()
    hash_int = int(hex_digest[:8], 16)
    
    # Base price range $45.00 - $225.00
    base_price = 45.0 + (hash_int % 180)
    
    # Calculate price using retailer multiplier and round to 2 decimal places
    final_price = round(base_price * config["price_multiplier"], 2)
    
    product_name = config["product_template"].format(query=clean_query)
    direct_link = f"{config['base_url']}{config['dummy_path'].format(query_slug=query_slug)}"
    
    return {
        "retailer": retailer_name,
        "product_name": product_name,
        "price_str": f"${final_price:.2f}",
        "link": direct_link,
        "is_simulated": True
    }


def scrape_retailer(retailer_name: str, query: str) -> Dict[str, Any]:
    """Queries a specific perfume retailer search page and parses the html.
    
    Falls back to dynamic simulation if blocked or scraping fails.
    """
    config = RETAILERS[retailer_name]
    query_encoded = urllib.parse.quote_plus(query)
    search_url = config["search_url"].format(query=query_encoded)

    try:
        # Try fetching real HTML content
        response = requests.get(search_url, headers=BROWSER_HEADERS, timeout=5)
        
        # If response is blocked, return simulated data
        if response.status_code != 200:
            return generate_deterministic_simulated_deal(retailer_name, query)
            
        soup = BeautifulSoup(response.text, "html.parser")
        selectors = config["selectors"]
        
        # Search for item container
        items = soup.select(selectors["item"])
        
        if not items:
            # Fallback to simulated data if no items parsed
            return generate_deterministic_simulated_deal(retailer_name, query)
            
        # Parse the first item found
        first_item = items[0]
        
        title_el = first_item.select_one(selectors["title"])
        price_el = first_item.select_one(selectors["price"])
        link_el = first_item.select_one(selectors["link"])
        
        if not title_el or not price_el:
            return generate_deterministic_simulated_deal(retailer_name, query)
            
        title = title_el.get_text(strip=True)
        price_str = price_el.get_text(strip=True)
        
        # Link resolution
        href = link_el.get("href", "") if link_el else ""
        if href.startswith("/"):
            link = f"{config['base_url']}{href}"
        elif href.startswith("http"):
            link = href
        else:
            link = search_url
            
        return {
            "retailer": retailer_name,
            "product_name": title,
            "price_str": price_str,
            "link": link,
            "is_simulated": False
        }
        
    except (requests.RequestException, Exception):
        # Fallback to simulated data on connection timeouts/failures
        return generate_deterministic_simulated_deal(retailer_name, query)


def scrape_all_retailers(query: str) -> List[Dict[str, Any]]:
    """Runs scraping across all 5 retailers for the given perfume query."""
    if not query or not query.strip():
        return []
        
    results = []
    for retailer in RETAILERS.keys():
        deal = scrape_retailer(retailer, query)
        results.append(deal)
        
    return results

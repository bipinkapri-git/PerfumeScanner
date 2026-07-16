"""Comparison logic for Perfume Scanner.

This module processes scraped product data, cleanses price strings,
sorts deals from cheapest to most expensive, and highlights the cheapest option.
"""

import re
from typing import Any, Dict, List


def clean_price(price_str: str) -> float:
    """Extracts a float value from a price string.
    
    Examples:
        "$104.99" -> 104.99
        "Sale Price: $95.50" -> 95.50
        "99.00" -> 99.0
        "Out of stock" -> float('inf')
    """
    if not price_str:
        return float("inf")
        
    # Strip whitespace, commas, and currency symbols
    price_str = price_str.replace(",", "").strip()
    
    # Use regex to find any floating point or decimal numbers
    match = re.search(r"\d+(?:\.\d+)?", price_str)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            pass
            
    return float("inf")


def process_and_compare_deals(deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Cleanses price strings, sorts deals, and flags the cheapest option.
    
    Returns:
        A dictionary containing:
        - "sorted_deals": List of deals sorted by numeric price (ascending)
        - "cheapest_deal": The cheapest deal dictionary, or None
        - "price_range": A tuple of (min_price, max_price)
    """
    if not deals:
        return {
            "sorted_deals": [],
            "cheapest_deal": None,
            "price_range": (0.0, 0.0)
        }
        
    processed_deals = []
    for deal in deals:
        cleaned_val = clean_price(deal.get("price_str", ""))
        deal_copy = deal.copy()
        deal_copy["price_val"] = cleaned_val
        processed_deals.append(deal_copy)
        
    # Sort deals. Put entries with float('inf') (failed parses) at the very end.
    sorted_deals = sorted(processed_deals, key=lambda x: x["price_val"])
    
    # Filter out infinite prices for the cheapest flag and range calculation
    valid_deals = [d for d in sorted_deals if d["price_val"] != float("inf")]
    
    cheapest_deal = None
    if valid_deals:
        cheapest_deal = valid_deals[0]
        # Flag the absolute cheapest option
        for deal in sorted_deals:
            if deal.get("retailer") == cheapest_deal["retailer"] and deal["price_val"] == cheapest_deal["price_val"]:
                deal["is_cheapest"] = True
            else:
                deal["is_cheapest"] = False
                
        prices = [d["price_val"] for d in valid_deals]
        price_range = (min(prices), max(prices))
    else:
        price_range = (0.0, 0.0)
        
    return {
        "sorted_deals": sorted_deals,
        "cheapest_deal": cheapest_deal,
        "price_range": price_range
    }

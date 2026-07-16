import unittest
from perfume_scanner.comparator import clean_price, process_and_compare_deals
from perfume_scanner.scraper import scrape_retailer, is_matching_product, resize_shopify_image


class TestPerfumeScanner(unittest.TestCase):
    """Test suite for Perfume Scanner components."""

    def test_clean_price(self):
        """Test extraction of floats from various price string formats."""
        self.assertEqual(clean_price("$104.99"), 104.99)
        self.assertEqual(clean_price("Sale: $95.50"), 95.50)
        self.assertEqual(clean_price("1,250.00"), 1250.0)
        self.assertEqual(clean_price("Free"), float("inf"))  # since there are no digits
        self.assertEqual(clean_price("Out of stock"), float("inf"))

    def test_process_and_compare_deals(self):
        """Test pricing sorting and cheapest flag assignment."""
        deals = [
            {"retailer": "FridayCharm", "price_str": "₹4,500.00", "link": "link1"},
            {"retailer": "Belvish", "price_str": "₹3,250.00", "link": "link2"},
            {"retailer": "Splash Fragrance", "price_str": "₹5,200.00", "link": "link3"},
        ]
        
        result = process_and_compare_deals(deals)
        sorted_deals = result["sorted_deals"]
        cheapest_deal = result["cheapest_deal"]
        
        self.assertEqual(len(sorted_deals), 3)
        self.assertEqual(cheapest_deal["retailer"], "Belvish")
        self.assertEqual(sorted_deals[0]["price_val"], 3250.0)
        self.assertEqual(sorted_deals[0]["is_cheapest"], True)
        self.assertEqual(sorted_deals[1]["is_cheapest"], False)

    def test_scraper_fallback(self):
        """Test that scraper returns None when a product is not found (no match)."""
        # A search query that does not exist should yield no product match, returning None
        deal = scrape_retailer("FridayCharm", "NonExistentFragranceName")
        self.assertIsNone(deal)

    def test_is_matching_product(self):
        """Test strict keyword matching, specifically decant and clone exclusions."""
        # Simple match
        self.assertTrue(is_matching_product("Rasasi Hawas", "Rasasi Hawas Pour Homme 100ml"))
        
        # Exclude decant if not searched
        self.assertFalse(is_matching_product("Rasasi Hawas", "Rasasi Hawas Decant 5ml"))
        # Allow decant if searched
        self.assertTrue(is_matching_product("Rasasi Hawas Decant", "Rasasi Hawas Decant 5ml"))
        
        # Exclude clones/impressions if not searched
        self.assertFalse(is_matching_product("Bleu de Chanel", "Bleu de Chanel Impression by Generic Brand"))
        # Allow clones if searched
        self.assertTrue(is_matching_product("Bleu de Chanel clone", "Bleu de Chanel clone 100ml"))

    def test_resize_shopify_image(self):
        """Test Shopify image CDN URL resize and {width} replacement."""
        url_with_width_var = "//cdn.shopify.com/products/image_{width}x.png?v=1"
        self.assertEqual(
            resize_shopify_image(url_with_width_var, 300),
            "//cdn.shopify.com/products/image_300x.png?v=1&width=300"
        )


if __name__ == "__main__":
    unittest.main()

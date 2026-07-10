import unittest
from perfume_scanner.comparator import clean_price, process_and_compare_deals
from perfume_scanner.scraper import generate_deterministic_simulated_deal, scrape_retailer


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
        
    def test_deterministic_simulation(self):
        """Test that simulated deals are structured correctly and stable."""
        deal1 = generate_deterministic_simulated_deal("Belvish", "Aventus")
        deal2 = generate_deterministic_simulated_deal("Belvish", "Aventus")
        
        # Check structure keys
        self.assertIn("retailer", deal1)
        self.assertIn("product_name", deal1)
        self.assertIn("price_str", deal1)
        self.assertIn("link", deal1)
        self.assertTrue(deal1["is_simulated"])
        
        # Check determinism: same query should yield same price
        self.assertEqual(deal1["price_str"], deal2["price_str"])
        self.assertEqual(deal1["product_name"], deal2["product_name"])

    def test_scraper_fallback(self):
        """Test that scraper falls back to simulation when given invalid input/failures."""
        # Querying with a dummy/empty state or hitting network timeouts will trigger fallback
        deal = scrape_retailer("Parcos", "NonExistentFragranceName")
        self.assertTrue(deal["is_simulated"])
        self.assertEqual(deal["retailer"], "Parcos")


if __name__ == "__main__":
    unittest.main()

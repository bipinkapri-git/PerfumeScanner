import unittest

from perfume_scanner.autocomplete import Trie, get_suggestions


class TestAutocomplete(unittest.TestCase):
    """Test suite for the Trie / fuzzy autocomplete engine."""

    def test_trie_prefix_match(self):
        """Trie should return names starting with a given prefix, case-insensitively."""
        trie = Trie(["Gucci Bloom", "Gucci Guilty", "Dior Sauvage"])

        results = trie.starts_with("gu")
        self.assertIn("Gucci Bloom", results)
        self.assertIn("Gucci Guilty", results)
        self.assertNotIn("Dior Sauvage", results)

    def test_trie_no_match_returns_empty(self):
        trie = Trie(["Gucci Bloom"])
        self.assertEqual(trie.starts_with("zzz"), [])

    def test_trie_respects_limit(self):
        trie = Trie(["Gucci Bloom", "Gucci Guilty", "Gucci Flora"])
        self.assertEqual(len(trie.starts_with("gu", limit=2)), 2)

    def test_get_suggestions_prefix(self):
        """Typing a valid prefix like 'Gu' should surface real Gucci entries."""
        suggestions = get_suggestions("Gu")
        self.assertTrue(any("Gucci" in s for s in suggestions))

    def test_get_suggestions_typo_tolerance(self):
        """Misspelling 'Gucci' as 'Guci' should still recommend a Gucci fragrance."""
        suggestions = get_suggestions("Guci")
        self.assertTrue(
            any("gucci" in s.lower() for s in suggestions),
            msg=f"Expected a Gucci suggestion for 'Guci', got: {suggestions}",
        )

    def test_get_suggestions_empty_query(self):
        self.assertEqual(get_suggestions(""), [])
        self.assertEqual(get_suggestions("   "), [])

    def test_get_suggestions_another_typo(self):
        """Misspelling 'Sauvage' as 'Savage' should still recommend Dior Sauvage."""
        suggestions = get_suggestions("Dior Savage")
        self.assertTrue(
            any("sauvage" in s.lower() for s in suggestions),
            msg=f"Expected Dior Sauvage for 'Dior Savage', got: {suggestions}",
        )


if __name__ == "__main__":
    unittest.main()

"""Static autocomplete catalog for Perfume Scanner's search box.

IMPORTANT: Perfume Scanner has no product database. Every search
triggers a live, on-demand scrape across 14 retailer storefronts (see
`scraper.py`) -- there is nothing to query for instant suggestions.

This module ships a small, hand-curated list of well-known fragrance
names that are commonly stocked by the Indian retailers in
`scraper.RETAILERS`, purely so the search box can offer fast,
typo-tolerant type-ahead suggestions (see `autocomplete.py` and
`search_widget.py`). It intentionally does NOT claim to be an
exhaustive or live product catalog -- it's a lightweight hint list.

Feel free to extend this list with more names as needed; it is plain
data with no dependencies.
"""

from __future__ import annotations

PERFUME_CATALOG: list[str] = [
    # Dior
    "Dior Sauvage",
    "Dior Sauvage Elixir",
    "Dior Homme Intense",
    "Miss Dior",
    "J'adore Dior",
    # Chanel
    "Bleu de Chanel",
    "Chanel No. 5",
    "Chanel Coco Mademoiselle",
    "Chanel Allure Homme Sport",
    # Creed
    "Creed Aventus",
    "Creed Aventus Cologne",
    "Creed Green Irish Tweed",
    "Creed Silver Mountain Water",
    "Creed Viking",
    # Gucci
    "Gucci Bloom",
    "Gucci Guilty",
    "Gucci Guilty Absolute",
    "Gucci Flora",
    "Gucci Memoire d'une Odeur",
    # Yves Saint Laurent
    "YSL Y Eau de Parfum",
    "YSL La Nuit de l'Homme",
    "YSL Black Opium",
    "YSL Libre",
    # Tom Ford
    "Tom Ford Oud Wood",
    "Tom Ford Tobacco Vanille",
    "Tom Ford Noir Extreme",
    "Tom Ford Ombre Leather",
    # Lattafa / Arabic house (very popular on Indian attar/oud retailers)
    "Lattafa Khamrah",
    "Lattafa Asad",
    "Lattafa Yara",
    "Lattafa Fakhar",
    "Lattafa Raghba",
    "Lattafa Qaed Al Fursan",
    "Lattafa Ana Abiyedh",
    # Rasasi
    "Rasasi Hawas",
    "Rasasi Hawas Pour Homme",
    "Rasasi Hawas Pour Femme",
    "Rasasi Rumz Al Rasasi",
    # Armaf
    "Armaf Club de Nuit Intense Man",
    "Armaf Club de Nuit Untold",
    "Armaf Tres Nuit",
    "Armaf Odyssey",
    # Al Haramain
    "Al Haramain Amber Oud",
    "Al Haramain L'Aventure",
    # Paco Rabanne
    "Paco Rabanne 1 Million",
    "Paco Rabanne Invictus",
    "Paco Rabanne Phantom",
    # Versace
    "Versace Eros",
    "Versace Dylan Blue",
    "Versace Pour Homme",
    # Giorgio Armani
    "Armani Code",
    "Armani Acqua di Gio",
    "Armani Stronger With You",
    # Jean Paul Gaultier
    "Jean Paul Gaultier Le Male",
    "Jean Paul Gaultier Scandal",
    # Montblanc
    "Montblanc Explorer",
    "Montblanc Legend",
    # Nishane
    "Nishane Hacivat",
    "Nishane Ani",
    # Xerjoff
    "Xerjoff Naxos",
    "Xerjoff Erba Pura",
    # Parfums de Marly
    "Parfums de Marly Layton",
    "Parfums de Marly Herod",
    # Amouage
    "Amouage Reflection Man",
    "Amouage Interlude",
    # Indian / desi favorites
    "Rasasi Blue Lady",
    "Skinn by Titan Celeste",
    "Ajmal Dahn Al Oudh",
    "Ajmal Shiro",
]

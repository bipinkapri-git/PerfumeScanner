import requests

def get_wikimedia_image(query: str) -> str:
    # Query Wikipedia for page images
    api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "titles": query,
        "pithumbsize": 500,
        "redirects": 1
    }
    try:
        response = requests.get(api_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "thumbnail" in page_data:
                    return page_data["thumbnail"]["source"]
    except Exception as e:
        print(f"Error querying Wikipedia: {e}")
    return ""

# Test popular perfumes
queries = ["Bleu de Chanel", "Creed Aventus", "Chanel No. 5", "Dior Sauvage"]
for q in queries:
    img = get_wikimedia_image(q)
    print(f"Query: {q} -> Image URL: {img}")

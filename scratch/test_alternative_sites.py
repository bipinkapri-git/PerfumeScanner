import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

sites = {
    "LaBellePerfumes": "https://labelleperfumes.com/search?q=aventus",
    "FragranceBuy": "https://fragrancebuy.ca/pages/search-results?q=aventus",
    "MaxAroma": "https://www.maxaroma.com/search?q=aventus"
}

for name, url in sites.items():
    try:
        print(f"\n--- Testing {name} ---")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        # Check if we can find images or product elements
        imgs = soup.find_all("img")
        print(f"Found {len(imgs)} images on page.")
        if len(imgs) > 0:
            for img in imgs[:5]:
                print(f"  Img Src: {img.get('src') or img.get('data-src') or ''}")
                
    except Exception as e:
        print(f"Error connecting to {name}: {e}")

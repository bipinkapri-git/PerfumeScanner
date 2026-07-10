import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

# Test Lattafa on Belvish and FridayCharm
sites = {
    "Belvish": "https://belvish.com/search?q=lattafa",
    "FridayCharm": "https://fridaycharm.com/search?q=lattafa",
    "PerfumePalace": "https://perfumepalace.in/search?q=lattafa"
}

for name, url in sites.items():
    try:
        print(f"\n--- Testing {name} ---")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.find("title")
        print(f"Title: {title_tag.text.strip() if title_tag else 'No title'}")
        
        # Check if the text contains lattafa (case insensitive)
        matches = len(soup.find_all(string=lambda text: text and "lattafa" in text.lower()))
        print(f"Found keyword matches: {matches}")
        
        # Save HTML for analysis
        filename = f"{name.lower()}_search.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.text[:50000])
        print(f"Saved first 50k chars of HTML to {filename}")
        
    except Exception as e:
        print(f"Error: {e}")

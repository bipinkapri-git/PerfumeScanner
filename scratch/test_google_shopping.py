import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/"
}

url = "https://www.google.com/search?tbm=shop&q=creed+aventus"
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Length: {len(response.text)}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    print(f"Title: {soup.title.text if soup.title else 'No title'}")
    
    # Save a snippet
    with open("google_shopping.html", "w", encoding="utf-8") as f:
        f.write(response.text[:20000])
    print("Saved first 20k chars to google_shopping.html")
    
except Exception as e:
    print(f"Error: {e}")

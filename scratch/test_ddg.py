import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

url = "https://html.duckduckgo.com/html/?q=creed+aventus+jomashop"
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Length: {len(response.text)}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    print(f"Title: {soup.title.text if soup.title else 'No title'}")
    
    # Print the first 5 result links
    results = soup.find_all("a", class_="result__url")
    print(f"Found {len(results)} results:")
    for r in results[:5]:
        print(f"Text: {r.text.strip()}, Link: {r.get('href', '')}")
        
except Exception as e:
    print(f"Error: {e}")

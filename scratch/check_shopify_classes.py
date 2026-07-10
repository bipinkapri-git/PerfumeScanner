import requests
from bs4 import BeautifulSoup
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

url = "https://labelleperfumes.com/search?q=aventus"
response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.text, "html.parser")

# Find divs with class names containing 'product' or 'grid' or 'card'
classes = set()
for tag in soup.find_all(class_=True):
    for c in tag.get('class'):
        if any(keyword in c.lower() for keyword in ['product', 'grid', 'card', 'item', 'price', 'money', 'search']):
            classes.add(c)

print("Found interesting class names:")
for c in sorted(classes):
    print(f"  {c}")

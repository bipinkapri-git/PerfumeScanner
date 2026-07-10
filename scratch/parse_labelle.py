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

# Let's search for typical Shopify product card selectors
# Often it is a div or li with a product-card related class or within grid__item
items = soup.find_all(class_=re.compile(r'product-card|grid__item|card--product|card-wrapper'))
print(f"Found {len(items)} matching product card elements.")

# Let's inspect some of them and try to extract Title, Price, Image, Link
for idx, item in enumerate(items[:5]):
    print(f"\n--- Item {idx+1} ---")
    
    # Try finding title
    title_el = item.find(class_=re.compile(r'title|name|card__heading'))
    title = title_el.text.strip() if title_el else "No title"
    
    # Try finding price
    price_el = item.find(class_=re.compile(r'price|money'))
    price = price_el.text.strip() if price_el else "No price"
    
    # Try finding image
    img_el = item.find("img")
    img_src = ""
    if img_el:
        img_src = img_el.get("src") or img_el.get("data-src") or ""
        if img_src.startswith("//"):
            img_src = "https:" + img_src
            
    # Try finding link
    link_el = item.find("a", href=True)
    link = "https://labelleperfumes.com" + link_el["href"] if link_el else "No link"
    
    print(f"Title: {title}")
    print(f"Price: {price}")
    print(f"Image: {img_src}")
    print(f"Link: {link}")

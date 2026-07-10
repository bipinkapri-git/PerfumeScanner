from bs4 import BeautifulSoup
import re
import urllib.parse

def parse_html_content(html_text: str, base_url: str, retailer_name: str) -> list:
    soup = BeautifulSoup(html_text, "html.parser")
    product_links = soup.find_all("a", href=re.compile(r'/products/'))
    
    seen_links = set()
    valid_items = []
    
    for link in product_links:
        href = link.get("href", "")
        if href.startswith("/"):
            prod_url = f"{base_url}{href}"
        else:
            prod_url = href
            
        clean_url = prod_url.split("?")[0]
        if clean_url in seen_links:
            continue
            
        parent = link
        card_container = None
        for _ in range(5):
            if parent is None:
                break
            p_class = " ".join(parent.get("class", [])) if parent.get("class") else ""
            if any(k in p_class.lower() for k in ["product", "card", "item", "grid__item", "grid-product"]):
                card_container = parent
                break
            parent = parent.parent
            
        if not card_container:
            card_container = link.parent
            
        title = ""
        title_el = card_container.find(class_=re.compile(r'title|name|heading|title-link'))
        if title_el:
            title = title_el.get_text(strip=True)
        if not title:
            title = link.get_text(strip=True)
            
        # Clean title text from extra spacing
        title = " ".join(title.split())
        
        if not title or len(title) < 5 or "rs." in title.lower() or "₹" in title.lower():
            continue
            
        price_str = ""
        price_el = card_container.find(class_=re.compile(r'price|money|sale-price'))
        if price_el:
            price_str = price_el.get_text(strip=True)
        else:
            price_text_el = card_container.find(string=re.compile(r'Rs\.|\bRs\b|₹'))
            if price_text_el:
                price_str = price_text_el.parent.get_text(strip=True)
                
        price_str = " ".join(price_str.split())
                
        image_url = ""
        img_el = card_container.find("img")
        if img_el:
            src = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy") or img_el.get("srcset") or ""
            if "," in src:
                src = src.split(",")[0].strip().split(" ")[0]
            if src.startswith("//"):
                image_url = f"https:{src}"
            elif src.startswith("http"):
                image_url = src
            elif src:
                image_url = f"{base_url}{src}"
                
        if title and price_str:
            seen_links.add(clean_url)
            valid_items.append({
                "retailer": retailer_name,
                "product_name": title,
                "price_str": price_str,
                "link": clean_url,
                "image_url": image_url,
                "is_simulated": False
            })
            
    return valid_items

# Test on local files
with open("belvish_full.html", "r", encoding="utf-8") as f:
    belvish_html = f.read()
belvish_items = parse_html_content(belvish_html, "https://belvish.com", "Belvish")
print(f"Belvish parsed: {len(belvish_items)} items")
for item in belvish_items[:3]:
    print(item)

with open("fridaycharm_full.html", "r", encoding="utf-8") as f:
    fc_html = f.read()
fc_items = parse_html_content(fc_html, "https://fridaycharm.com", "FridayCharm")
print(f"\nFridayCharm parsed: {len(fc_items)} items")
for item in fc_items[:3]:
    print(item)

from bs4 import BeautifulSoup
import re

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
            
        # Heuristic card container: traverse up to find the first parent that has a price
        parent = link.parent
        card_container = None
        for _ in range(6):
            if parent is None:
                break
            # Does this parent contain a price?
            if parent.find(class_=re.compile(r'price|money|sale-price')) or parent.find(string=re.compile(r'Rs\.|\bRs\b|₹')):
                card_container = parent
                break
            parent = parent.parent
            
        if not card_container:
            continue
            
        # Title: try common heading tags or classes, otherwise use the link text itself
        title = ""
        title_el = card_container.find(class_=re.compile(r'title|name|heading|card__heading'))
        if title_el:
            title = title_el.get_text(strip=True)
        if not title:
            title = link.get_text(strip=True)
            
        title = " ".join(title.split())
        
        # Clean out any accidental price tags inside the title text
        if not title or len(title) < 5 or "rs." in title.lower() or "₹" in title.lower():
            continue
            
        # Price: extract from price classes or text
        price_str = ""
        price_el = card_container.find(class_=re.compile(r'price|money|sale-price'))
        if price_el:
            # If the price element has a sale and regular price, try getting the sale price first
            sale_el = price_el.find(class_=re.compile(r'sale|active'))
            if sale_el:
                price_str = sale_el.get_text(strip=True)
            else:
                price_str = price_el.get_text(strip=True)
        
        if not price_str:
            price_text_el = card_container.find(string=re.compile(r'Rs\.|\bRs\b|₹'))
            if price_text_el:
                price_str = price_text_el.parent.get_text(strip=True)
                
        price_str = " ".join(price_str.split())
        
        # Extract image URL
        image_url = ""
        # Search for any img tags in the container
        imgs = card_container.find_all("img")
        for img_el in imgs:
            # Check lazy-loading attributes
            src = (img_el.get("src") or 
                   img_el.get("data-src") or 
                   img_el.get("data-lazy") or 
                   img_el.get("srcset") or 
                   img_el.get("data-srcset") or "")
            
            # If multiple sources in srcset, pick the first
            if "," in src:
                src = src.split(",")[0].strip().split(" ")[0]
                
            if not src or "logo" in src.lower() or "icon" in src.lower():
                continue
                
            if src.startswith("//"):
                image_url = f"https:{src}"
            elif src.startswith("http"):
                image_url = src
            else:
                image_url = f"{base_url}{src}"
            break
            
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

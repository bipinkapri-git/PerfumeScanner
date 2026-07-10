from bs4 import BeautifulSoup
import re

files = ["belvish_full.html", "fridaycharm_full.html"]

for filename in files:
    print(f"\n==========================================")
    print(f"Analyzing {filename}")
    print(f"==========================================")
    with open(filename, "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Look for links containing "/products/" and inspect their elements
    links = soup.find_all("a", href=re.compile(r'/products/'))
    print(f"Total product links found: {len(links)}")
    
    # Print first few unique links
    unique_links = []
    seen = set()
    for l in links:
        href = l["href"]
        if href not in seen and l.text.strip():
            seen.add(href)
            unique_links.append(l)
            
    print("\nUnique Product Links (Sample):")
    for link in unique_links[:5]:
        print(f"  Text: {link.text.strip()}")
        print(f"  Href: {link['href']}")
        # Let's inspect the HTML of the link's parent card container
        # We find parent elements with classes
        parent = link.parent
        classes = []
        while parent and len(classes) < 3:
            if parent.get("class"):
                classes.append((parent.name, parent.get("class")))
            parent = parent.parent
        print(f"  Parent ancestry: {classes}")

    # 2. Look for product images containing 'cdn.shopify.com' or 'products'
    imgs = soup.find_all("img")
    product_imgs = []
    for img in imgs:
        src = img.get("src") or img.get("data-src") or img.get("data-lazy") or ""
        if "cdn.shopify.com" in src or "/products/" in src:
            product_imgs.append(src)
            
    print(f"\nTotal product images: {len(product_imgs)}")
    print("Sample Image URLs:")
    for img in product_imgs[:5]:
        print(f"  {img}")

from bs4 import BeautifulSoup
import re

files = ["belvish_search.html", "fridaycharm_search.html", "perfumepalace_search.html"]

for filename in files:
    print(f"\n==========================================")
    print(f"Analyzing {filename}")
    print(f"==========================================")
    with open(filename, "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    # Standard Shopify selectors check
    # Let's search for image tags and list their parents
    imgs = soup.find_all("img")
    print(f"Total images: {len(imgs)}")
    
    # Print first few images that look like product images
    product_imgs = []
    for img in imgs:
        src = img.get("src") or img.get("data-src") or ""
        alt = img.get("alt", "").lower()
        if "logo" not in src.lower() and "icon" not in src.lower() and src:
            product_imgs.append((src, alt, img.parent.name, img.parent.get("class", [])))
            
    print("\nSample Product Images:")
    for img in product_imgs[:5]:
        print(f"  src: {img[0][:75]}\n  alt: {img[1]}\n  parent: {img[2]}, class: {img[3]}")
        
    # Let's find elements containing prices (INR Rs. symbol or "rs" or "Rs")
    print("\nSample Prices:")
    price_tags = []
    # Search for Rs. or rupee symbol in text
    for tag in soup.find_all(string=re.compile(r'Rs\.|\bRs\b|₹')):
        parent = tag.parent
        price_tags.append((tag.strip(), parent.name, parent.get("class", [])))
    
    for pt in price_tags[:5]:
        print(f"  text: {pt[0]}, tag: {pt[1]}, class: {pt[2]}")

    # Let's search for links to products (containing "/products/")
    print("\nSample Product Links:")
    links = soup.find_all("a", href=re.compile(r'/products/'))
    for link in links[:5]:
        print(f"  text: {link.text.strip()}, href: {link['href']}")

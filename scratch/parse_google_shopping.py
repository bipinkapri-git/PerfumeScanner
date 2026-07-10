from bs4 import BeautifulSoup
import re

with open("google_shopping.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Let's search for elements containing "$"
prices = []
for el in soup.find_all(string=re.compile(r'\$\d+')):
    parent = el.parent
    # print parent tag and class
    prices.append((el.strip(), parent.name, parent.get('class', [])))

print("Found prices:")
for p in prices[:15]:
    print(p)

# Let's search for image tags
imgs = soup.find_all("img")
print(f"\nFound {len(imgs)} images:")
for img in imgs[:10]:
    print(f"src: {img.get('src', '')[:50]}, alt: {img.get('alt', '')}")

# Let's search for links containing "/shopping/product/" or standard search outbound links
links = soup.find_all("a", href=True)
print(f"\nFound {len(links)} links:")
for a in links[:15]:
    print(f"href: {a['href'][:70]}, text: {a.text.strip()}")

import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

# Download complete HTML
urls = {
    "belvish": "https://belvish.com/search?q=lattafa",
    "fridaycharm": "https://fridaycharm.com/search?q=lattafa"
}

for name, url in urls.items():
    try:
        response = requests.get(url, headers=headers, timeout=10)
        with open(f"{name}_full.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"Successfully downloaded full HTML for {name} ({len(response.text)} bytes)")
    except Exception as e:
        print(f"Error: {e}")

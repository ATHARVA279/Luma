import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AI-Learning-Navigator/1.0; +https://example.com)"
}

def extract_text_from_url(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    for s in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        s.decompose()

    texts = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        t = tag.get_text(" ", strip=True)
        if t:
            texts.append(t)

    full = "\n\n".join(texts)

    cleaned = re.sub(r"\s{2,}", " ", full)
    cleaned = re.sub(r"\u200b", "", cleaned)
    cleaned = cleaned.strip()

    return cleaned

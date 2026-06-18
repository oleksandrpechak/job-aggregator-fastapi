from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

def build_dedup_key(source: str, link: str) -> str:
    return f"{source}:{normalize_url(link)}"
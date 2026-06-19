from urllib.parse import urlparse, urlunparse
import re
from datetime import datetime, timezone

def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

def build_dedup_key(source: str, link: str) -> str:
    return f"{source}:{normalize_url(link)}"

UKRAINIAN_MONTHS = {
    "січня": 1, "лютого": 2, "березня": 3, "квітня": 4,
    "травня": 5, "червня": 6, "липня": 7, "серпня": 8,
    "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12,
}

def parse_dou_date(raw: str) -> datetime | None:
    """Parses DOU's 'D <month genitive>' format (e.g. '16 червня').
    DOU omits the year, so it's inferred relative to today."""
    if not raw:
        return None
    match = re.match(r"(\d{1,2})\s+([а-яіїєґ]+)", raw.strip().lower())
    if not match:
        return None
    day, month_name = int(match.group(1)), match.group(2)
    month = UKRAINIAN_MONTHS.get(month_name)
    if month is None:
        return None

    today = datetime.now(timezone.utc)
    try:
        candidate = datetime(today.year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None

    if candidate.date() > today.date():
        candidate = candidate.replace(year=today.year - 1)
    return candidate
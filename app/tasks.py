import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pymongo import UpdateOne
from app.celery_app import celery_app
from app.db_sync import sync_job_collection
from app.utils import build_dedup_key, parse_dou_date
from urllib.parse import urljoin
from app.config import settings
import logging


logger = logging.getLogger(__name__)

DOU_SOURCE_URL = settings.dou_source_url
DOU_SOURCE_NAME = settings.dou_source_name

def fetch_html(url: str) -> str | None:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "job-aggregator-bot/0.1"},
            timeout=10
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        logger.exception("Failed to fetch DOU jobs page: &s", url)
        return None


def parse_dou_listing(item) -> dict | None:
    try:
        title_el = item.select_one(".title")
        company_el = item.select_one(".company")
        link_el = item.select_one(".title a")
        date_el = item.select_one(".date")

        if not title_el or not link_el:
            return None

        href = link_el.get("href")
        if not href:
            return None

        title = title_el.get_text(strip=True)
        company = company_el.get_text(strip=True) if company_el else None
        link = urljoin(DOU_SOURCE_URL, href)

        raw_date = date_el.get_text(strip=True) if date_el else None
        posted_at = parse_dou_date(raw_date)

        if raw_date and posted_at is None:
            logger.warning(
                "Unparseable date '%s' for %s — storing posted_at=None",
                raw_date,
                link,
            )

        dedup_key = build_dedup_key(DOU_SOURCE_NAME, link)

        return {
            "title": title,
            "company": company,
            "level": "junior",
            "link": link,
            "posted_at": posted_at,
            "source": DOU_SOURCE_NAME,
            "dedup_key": dedup_key,
            "scraped_at": datetime.now(timezone.utc),
        }

    except Exception:
        logger.exception("Failed to parse one DOU listing")
        return None


@celery_app.task(name="app.tasks.ingest_dou_jobs")
def ingest_dou_jobs():
    html =html = fetch_html(DOU_SOURCE_URL)
    if html is None:
        return {
            "status": "failed",
            "reason": "http_error",
            "matched": 0,
            "upserted": 0,
            "skipped": 0,
        }

    soup = BeautifulSoup(html, "html.parser")
    listings = soup.select(".l-vacancy")

    operations = []
    skipped = 0

    for item in listings:
        job_doc = parse_dou_listing(item)
        if job_doc is None:
            skipped += 1
            continue
        operations.append(
            UpdateOne(
                {"dedup_key": job_doc["dedup_key"]},
                {"$set": job_doc},
                upsert=True,
            )
        )
    if not operations:
        return {
            "status": "ok",
            "matched": 0,
            "upserted": 0,
            "skipped": skipped,
        }
    result = sync_job_collection.bulk_write(operations)
    return {
        "status": "ok",
        "matched": result.matched_count,
        "upserted": len(result.upserted_ids),
        "skipped": skipped,
    }
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pymongo import UpdateOne
from app.celery_app import celery_app
from app.db_sync import sync_job_collection
from app.utils import build_dedup_key
from urllib.parse import urljoin
from app.config import settings

DOU_SOURCE_URL = settings.dou_source_url
DOU_SOURCE_NAME = settings.dou_source_name

@celery_app.task(name="app.tasks.ingest_dou_jobs")
def ingest_dou_jobs():
    response = requests.get(DOU_SOURCE_URL, headers={"User-Agent": "job-aggregator-bot/0.1"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    listings = soup.select(".l-vacancy")
    operations = []

    for item in listings:
        title_el = item.select_one(".title")
        company_el = item.select_one(".company") 
        link_el = item.select_one(".title a")
        date_el = item.select_one(".date")
        raw_date = date_el.get_text(strip=True)

        if not title_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        company = company_el.get_text(strip=True) if company_el else None
        link = urljoin(DOU_SOURCE_URL, link_el.get("href"))
        posted_at = raw_date

        dedup_key = build_dedup_key(DOU_SOURCE_NAME, link)
        job_doc = {
            "title": title,
            "company": company,
            "level": "junior",
            "link": link,
            "posted_at": posted_at,
            "source": DOU_SOURCE_NAME,
            "dedup_key": dedup_key,
            "scraped_at": datetime.now(timezone.utc),
        }
        operations.append(
            UpdateOne({"dedup_key": dedup_key}, {"$set": job_doc}, upsert=True)
        )

    if not operations:
        return {"matched": 0, "upserted": 0}

    result = sync_job_collection.bulk_write(operations)
    return {"matched": result.matched_count, "upserted": len(result.upserted_ids)}
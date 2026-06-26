import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import UpdateOne
from app.celery_app import celery_app
from app.db_sync import sync_job_collection, sync_db
from app.utils import build_dedup_key, parse_dou_date
from urllib.parse import urljoin
from app.config import settings
from app.services.matching import job_matches_filter
from pymongo.errors import DuplicateKeyError
from app.services.discord import send_discord_job_alert
import logging


logger = logging.getLogger(__name__)

USER_AGENT = "job-aggregator-bot/0.1"
DOU_SOURCE_URL = settings.dou_source_url
DOU_SOURCE_NAME = settings.dou_source_name

def fetch_html(url: str) -> str | None:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        logger.exception("Failed to fetch DOU jobs page: %s", url)
        return None


def parse_dou_listing(
        item,
        base_url: str,
        source: str,
        source_name: str
        ) -> dict | None:
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
        link = urljoin(base_url, href)

        raw_date = date_el.get_text(strip=True) if date_el else None
        posted_at = parse_dou_date(raw_date)

        if raw_date and posted_at is None:
            logger.warning(
                "Unparseable date '%s' for %s",
                raw_date,
                link,
            )

        dedup_key = build_dedup_key(source, link)

        return {
            "title": title,
            "company": company,
            "level": "junior",
            "link": link,
            "posted_at": posted_at,
            "source": source,
            "source_name": source_name,
            "dedup_key": dedup_key,
            "scraped_at": datetime.now(timezone.utc),
        }

    except Exception:
        logger.exception("Failed to parse one DOU listing")
        return None
    
def get_scraper_config(config_id: str) -> dict | None:
    if not ObjectId.is_valid(config_id):
        return None
    return sync_db.scraper_configs.find_one({
        "_id": ObjectId(config_id)
    })


def find_unalerted_matching_jobs(filter_doc: dict) -> list[dict]:
    sent_job_ids = sync_db.alerts_sent.distinct(
        "job_id",
        {"filter_id": filter_doc["_id"]},
    )
    job_query = {
        "_id": {"$nin": sent_job_ids},
    }
    if filter_doc.get("source"):
        job_query["source"] = filter_doc["source"]

    jobs = sync_db.jobs.find(job_query)
    matching_jobs = []
    for job in jobs:
        if job_matches_filter(job, filter_doc):
            matching_jobs.append(job)

    return matching_jobs

def send_alert_once(job: dict, filter_doc: dict) -> bool:
    alert_doc = {
        "job_id": job["_id"],
        "filter_id": filter_doc["_id"],
        "sent_at": datetime.now(timezone.utc),
        "webhook_status": 0,
    }

    try:
        sync_db.alerts_sent.insert_one(alert_doc)
    except DuplicateKeyError:
        return False

    try:
        status_code = send_discord_job_alert(
            webhook_url=filter_doc["discord_webhook"],
            job=job,
        )

        sync_db.alerts_sent.update_one(
            {
                "job_id": job["_id"],
                "filter_id": filter_doc["_id"],
            },
            {
                "$set": {
                    "webhook_status": status_code,
                }
            },
        )

        return True

    except Exception:
        logger.exception(
            "Failed to send Discord alert for job_id=%s filter_id=%s",
            job["_id"],
            filter_doc["_id"],
        )

        sync_db.alerts_sent.update_one(
            {
                "job_id": job["_id"],
                "filter_id": filter_doc["_id"],
            },
            {
                "$set": {
                    "webhook_status": -1,
                }
            },
        )

        return False
    

@celery_app.task(name="app.tasks.ingest_dou")
def ingest_dou(config_id: str):
    logger.info("scraper_config: loading config_id=%s", config_id)
    if not ObjectId.is_valid(config_id):
        logger.info("scraper_config: skipped invalid_config_id config_id=%s", config_id)
        return {
            "skipped": True,
            "reason": "invalid_config_id",
            "config_id": config_id
        }

    config = get_scraper_config(config_id)
    if not config:
        logger.info("scraper_config: skipped config_not_found config_id=%s", config_id)
        return {
            "skipped": True,
            "reason": "config_not_found",
            "config_id": config_id
        }
    if not config.get("active", False):
        logger.info("scraper_config: skipped inactive config_id=%s", config_id)
        return {
            "skipped": True,
            "reason": "config_inactive",
            "config_id": config_id
        }
    source = config["source"]
    source_name = config["name"]
    url = config["url"]
    logger.info(
        "scraper_config: loaded config_id=%s source=%s name=%s url=%s active=%s",
        config_id,
        source,
        source_name,
        url,
        bool(config.get("active", False)),
    )
    html = fetch_html(url)
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
    if not listings:
        logger.info("scraping: no_listings config_id=%s source=%s", config_id, source)

    operations = []
    skipped = 0

    for item in listings:
        job_doc = parse_dou_listing(
            item=item,
            base_url=url,
            source=source,
            source_name=source_name
            )
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
        logger.info(
            "scraping: result config_id=%s parsed=%d skipped=%d matched=%d upserted=%d",
            config_id,
            0,
            skipped,
            0,
            0,
        )
        return {
            "status": "ok",
            "matched": 0,
            "upserted": 0,
            "skipped": skipped,
            "filter_matches": 0
        }
    result = None

    if operations:
        result = sync_job_collection.bulk_write(operations)

    active_filters = list(sync_db.filters.find({"active": True}))
    logger.info(
        "filter_matching: active_filters=%d config_id=%s",
        len(active_filters),
        config_id,
    )
    filter_matches = 0
    alerts_sent = 0
    for filter_doc in active_filters:
        matching_jobs = find_unalerted_matching_jobs(filter_doc)
        filter_matches += len(matching_jobs)
        for job in matching_jobs:
            was_sent = send_alert_once(job, filter_doc)
            if was_sent:
                alerts_sent += 1
    logger.info(
        "filter_matching: summary config_id=%s matched_jobs=%d alerts_sent=%d",
        config_id,
        filter_matches,
        alerts_sent,
    )
    logger.info(
        "scraping: result config_id=%s parsed=%d skipped=%d matched=%d upserted=%d",
        config_id,
        len(operations),
        skipped,
        result.matched_count if result else 0,
        result.upserted_count if result else 0,
    )
    return {
        "status": "ok",
        "matched": result.matched_count if result else 0,
        "upserted": result.upserted_count if result else 0,
        "skipped": skipped,
        "filter_matches": filter_matches,
        "alerts_sent": alerts_sent
    }

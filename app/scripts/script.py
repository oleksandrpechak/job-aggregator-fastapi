from app.db_sync import sync_db
from app.schemas.schemas import ScraperConfigCreate


config = ScraperConfigCreate(
    name="dou_python",
    source="dou",
    url="https://jobs.dou.ua/vacancies/?category=Python",
    active=True,
    schedule_hours=2,
)

doc = config.model_dump(mode="json")

result = sync_db.scraper_configs.update_one(
    {"name": doc["name"], "source": doc["source"]},
    {"$set": doc},
    upsert=True,
)

config_doc = sync_db.scraper_configs.find_one({
    "name": doc["name"],
    "source": doc["source"],
})

print(str(config_doc["_id"]))
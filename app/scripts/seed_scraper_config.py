from app.db_sync import sync_db
from app.schemas.schemas import ScraperConfigCreate
from app.utils import build_dou_category_url


def upsert_dou_config(category: str, name: str):
    config = ScraperConfigCreate(
        name=name,
        source="dou",
        url=build_dou_category_url(category),
        active=True,
        schedule_hours=2,
    )

    doc = config.model_dump(mode="json")

    result = sync_db.scraper_configs.update_one(
        {"name": doc["name"], "source": doc["source"]},
        {"$set": doc},
        upsert=True,
    )

    saved = sync_db.scraper_configs.find_one({
        "name": doc["name"],
        "source": doc["source"],
    })

    print(f"{name}: {saved['_id']} -> {saved['url']}")


if __name__ == "__main__":
    upsert_dou_config(category="Ruby", name="dou_ruby")
# Job Aggregation Platform

A FastAPI-based job aggregation platform that scrapes job listings from DOU, stores them in MongoDB, matches jobs against saved filters, and sends Discord alerts when matching jobs are found.

## Tech Stack

* Python 3.11+
* FastAPI
* MongoDB
* PyMongo / AsyncMongoClient
* Celery
* Celery Beat
* Redis
* BeautifulSoup
* Discord Webhooks
* Docker / Docker Compose
* Pydantic v2

## Features

* REST API for job CRUD operations
* API key protection for write operations
* MongoDB as the primary database
* Scheduled scraping with Celery Beat
* Scraper configs stored in MongoDB
* DOU scraper with category-based URLs
* Job deduplication using normalized URLs
* User-defined alert filters
* Discord webhook alerts for matching jobs
* Duplicate alert prevention with `alerts_sent`
* Basic test coverage for matching, parsing, deduplication, and filters

## Architecture Flow

```text
Celery Beat
→ ingest_dou(config_id)
→ load scraper config from MongoDB
→ scrape DOU jobs
→ normalize and save jobs
→ load active filters
→ match jobs against filters
→ send Discord webhook alert
→ save alert record
```

## Main Collections

### jobs

Stores scraped job listings.

```json
{
  "title": "Junior Python Developer",
  "company": "Example Company",
  "level": "junior",
  "link": "https://jobs.dou.ua/...",
  "source": "dou",
  "source_name": "dou_python",
  "dedup_key": "dou:https://jobs.dou.ua/...",
  "scraped_at": "...",
  "posted_at": "..."
}
```

### scraper_configs

Stores scraper settings.

```json
{
  "name": "dou_python",
  "source": "dou",
  "url": "https://jobs.dou.ua/vacancies/?category=Python",
  "active": true,
  "schedule_hours": 2
}
```

### filters

Stores alert preferences.

```json
{
  "level": "junior",
  "stack": ["python", "fastapi"],
  "source": "dou",
  "discord_webhook": "https://discord.com/api/webhooks/...",
  "active": true
}
```

### alerts_sent

Prevents duplicate Discord alerts.

```json
{
  "job_id": "...",
  "filter_id": "...",
  "sent_at": "...",
  "webhook_status": 204
}
```

## API Endpoints

### Health

```http
GET /health
GET /redis-health
```

### Jobs

```http
POST /jobs
GET /jobs/
GET /jobs/{id}
PUT /jobs/{id}
DELETE /jobs/{id}
```

### Filters

```http
POST /filters/
GET /filters/
GET /filters/{id}
PUT /filters/{id}
DELETE /filters/{id}
```

Filter routes are protected by API key because they may contain Discord webhook URLs.

## Environment Variables

Example `.env`:

```env
MONGODB_URI=mongodb://mongo:27017
DATABASE_NAME=job_aggregator
REDIS_URL=redis://redis:6379/0
API_KEY=your_api_key
DEFAULT_DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
```

## Running with Docker

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

## Running Tests

```bash
python -m pytest -q
```

With Docker:

```bash
docker compose exec api python -m pytest -q
```

## Current Limitations

* Only DOU is implemented as a source.
* DOU categories such as Python and Ruby are configured separately.
* Matching is keyword-based and does not use an LLM.
* Stack matching is limited by the scraped job text.
* No user accounts yet; filters are global/admin-managed.
* Celery Beat schedule is semi-dynamic: adding a new scraper config also requires adding a Beat entry and restarting Beat.

## Future Improvements

* Add job detail page scraping for better stack matching.
* Add another job source.
* Improve experience level extraction.
* Add `match_mode` support: `all` / `any`.
* Add more tests around Discord alerting with mocked requests.
* Add user-specific filters.

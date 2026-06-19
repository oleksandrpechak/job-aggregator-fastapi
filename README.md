# job-aggregator-fastapi

A FastAPI project that scrapes job listings and stores them in MongoDB.

## Features
- REST API for job CRUD operations
- MongoDB as the primary datastore
- Redis-backed Celery worker for background scraping tasks
- `/docs` available for API exploration
- Job scraping endpoint: `POST /scrape/dou`
- docker-compose

## Requirements
- Python 3.11
- MongoDB
- Redis
- Docker / Docker Compose (optional)

## API Endpoints
- `GET /health`
- `GET /redis-health`
- `POST /jobs`
- `GET /jobs/`
- `GET /jobs/{id}`
- `PUT /jobs/{id}`
- `DELETE /jobs/{id}`
- `POST /scrape/dou`

## Notes
- Background scraping is handled by Celery using Redis.
- `posted_at` is parsed from scraped job post dates.
- `/docs` provides interactive API documentation.

from pymongo import AsyncMongoClient
from app.config import settings

uri = settings.mongodb_uri

client = AsyncMongoClient(uri)

db = client[settings.database_name]
job_collection = db.jobs
filter_collection = db.filters
alerts_sent_collection = db.alerts_sent



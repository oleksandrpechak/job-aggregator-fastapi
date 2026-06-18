from pymongo import MongoClient
from app.config import settings

sync_client = MongoClient(settings.mongodb_uri)
sync_db = sync_client[settings.database_name]
sync_job_collection = sync_db["jobs"]
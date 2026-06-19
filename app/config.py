from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongodb_uri: str
    database_name: str
    redis_host: str
    redis_port: int
    redis_db: int
    redis_url: str
    celery_app_timezone: str
    dou_source_name: str
    dou_source_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
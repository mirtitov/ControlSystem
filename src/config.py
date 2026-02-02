from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/production_control"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery
    celery_broker_url: str = "amqp://admin:admin@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"
    
    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    
    # Application
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"
    
    # MinIO Buckets
    minio_buckets: list[str] = ["reports", "exports", "imports"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

"""
Script to initialize MinIO buckets.
Run this once to create required buckets.
"""
from src.services.minio_service import minio_service

if __name__ == "__main__":
    print("Initializing MinIO buckets...")
    minio_service._initialize_buckets()
    print("✅ MinIO buckets initialized!")

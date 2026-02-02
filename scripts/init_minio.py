"""
Script to initialize MinIO buckets.
Run this once to create required buckets.
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.services.minio_service import minio_service

    if __name__ == "__main__":
        print("Initializing MinIO buckets...")
        minio_service._initialize_buckets()
        print("✅ MinIO buckets initialized!")
except ImportError as e:
    print(f"⚠️  Could not import minio_service: {e}")
    print("   MinIO buckets will be created automatically on first use.")
    sys.exit(0)

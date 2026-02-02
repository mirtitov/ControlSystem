import os
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from src.config import settings


class MinIOService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._initialize_buckets()

    def _initialize_buckets(self):
        """Initialize required buckets if they don't exist"""
        for bucket_name in settings.minio_buckets:
            try:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    print(f"✅ Created bucket: {bucket_name}")
            except S3Error as e:
                print(f"❌ Error creating bucket {bucket_name}: {e}")

    def upload_file(
        self,
        bucket: str,
        file_path: str,
        object_name: str | None = None,
        expires_days: int = 7,
    ) -> str:
        """
        Upload file to MinIO and return pre-signed URL.

        Args:
            bucket: Bucket name
            file_path: Local file path
            object_name: Object name in MinIO (default: filename)
            expires_days: URL expiration in days

        Returns:
            Pre-signed URL for downloading
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            # Upload file
            self.client.fput_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=file_path,
                content_type=self._get_content_type(file_path),
            )

            # Get pre-signed URL
            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=timedelta(days=expires_days),
            )

            return url
        except S3Error as e:
            raise Exception(f"Failed to upload file to MinIO: {e}") from e

    def upload_bytes(
        self,
        bucket: str,
        data: bytes,
        object_name: str,
        content_type: str | None = None,
        expires_days: int = 7,
    ) -> str:
        """
        Upload bytes data to MinIO.

        Args:
            bucket: Bucket name
            data: Bytes data
            object_name: Object name in MinIO
            content_type: Content type (auto-detected if None)
            expires_days: URL expiration in days

        Returns:
            Pre-signed URL
        """
        from io import BytesIO

        if content_type is None:
            content_type = self._get_content_type_by_extension(object_name)

        try:
            data_stream = BytesIO(data)
            self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=data_stream,
                length=len(data),
                content_type=content_type,
            )

            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=timedelta(days=expires_days),
            )

            return url
        except S3Error as e:
            raise Exception(f"Failed to upload bytes to MinIO: {e}") from e

    def download_file(self, bucket: str, object_name: str, file_path: str):
        """Download file from MinIO"""
        try:
            self.client.fget_object(
                bucket_name=bucket, object_name=object_name, file_path=file_path
            )
        except S3Error as e:
            raise Exception(f"Failed to download file from MinIO: {e}") from e

    def download_bytes(self, bucket: str, object_name: str) -> bytes:
        """Download file as bytes from MinIO"""
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise Exception(f"Failed to download bytes from MinIO: {e}") from e

    def delete_file(self, bucket: str, object_name: str):
        """Delete file from MinIO"""
        try:
            self.client.remove_object(bucket, object_name)
        except S3Error as e:
            raise Exception(f"Failed to delete file from MinIO: {e}") from e

    def list_files(self, bucket: str, prefix: str | None = None):
        """List files in bucket"""
        try:
            objects = self.client.list_objects(bucket_name=bucket, prefix=prefix, recursive=True)
            return list(objects)
        except S3Error as e:
            raise Exception(f"Failed to list files from MinIO: {e}") from e

    def _get_content_type(self, file_path: str) -> str:
        """Determine Content-Type from file path"""
        return self._get_content_type_by_extension(file_path)

    def _get_content_type_by_extension(self, file_path: str) -> str:
        """Determine Content-Type from file extension"""
        ext = os.path.splitext(file_path)[1].lower()

        content_types = {
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".csv": "text/csv",
            ".pdf": "application/pdf",
            ".json": "application/json",
        }

        return content_types.get(ext, "application/octet-stream")

    def get_file_size(self, bucket: str, object_name: str) -> int:
        """Get file size in bytes"""
        try:
            stat = self.client.stat_object(bucket, object_name)
            return stat.size
        except S3Error as e:
            raise Exception(f"Failed to get file size from MinIO: {e}") from e


# Singleton instance
minio_service = MinIOService()

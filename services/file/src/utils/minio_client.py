"""
Utility to obtain a MinIO client instance.
"""

from minio import Minio

from src.config import settings

_minio_client = None


def get_minio_client() -> Minio:
    """Return a singleton MinIO client.
    The client is lazily created on first call.
    """
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        # Ensure bucket exists
        if not _minio_client.bucket_exists(settings.minio_bucket):
            _minio_client.make_bucket(settings.minio_bucket)
    return _minio_client

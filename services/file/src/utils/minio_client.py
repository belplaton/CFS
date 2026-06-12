"""
MinIO helpers for File Service.

Object-key layout (per user)::

    {user_id}/{files|trash|preview}/{uuid}{ext}

The ``files`` and ``trash`` prefixes are used for normal and soft-deleted
objects respectively. The ``preview`` prefix is reserved for the Preview
service.
"""

from __future__ import annotations

import io
import uuid as uuidlib
from datetime import timedelta
from typing import BinaryIO, Optional
from uuid import UUID

from minio import Minio
from minio.commonconfig import CopySource
from minio.error import S3Error

from src.config import settings
from src.utils.logging import get_logger


logger = get_logger(__name__)


# ==================== Singleton ====================

_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    """Return a lazily-initialised singleton MinIO client."""
    global _client
    if _client is None:
        _client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        _ensure_bucket(_client)
    return _client


def reset_minio_client() -> None:
    """Reset the singleton (used by tests that mock the client)."""
    global _client
    _client = None


def _ensure_bucket(client: Minio) -> None:
    bucket = settings.minio_bucket
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info("minio.bucket.created", bucket=bucket)
    except S3Error as exc:
        logger.warning("minio.bucket.ensure_failed", bucket=bucket, error=str(exc))


# ==================== Object-key helpers ====================


def files_object_key(user_id: UUID, ext: str) -> str:
    """Build a unique key for a newly uploaded file."""
    return f"{user_id}/{settings.minio_prefix_files}/{uuidlib.uuid4()}{_ext(ext)}"


def trash_object_key(user_id: UUID, ext: str) -> str:
    """Build the key used when the file is soft-deleted."""
    return f"{user_id}/{settings.minio_prefix_trash}/{uuidlib.uuid4()}{_ext(ext)}"


def _ext(ext: str) -> str:
    ext = (ext or "").lower().lstrip(".")
    return f".{ext}" if ext else ""


def extract_extension(object_name: str) -> str:
    """Return the lowercased extension (no dot) of a stored object key."""
    if "." not in object_name.rsplit("/", 1)[-1]:
        return ""
    return object_name.rsplit(".", 1)[-1].lower()


# ==================== High-level operations ====================


def put_bytes(
    bucket: str,
    object_name: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> None:
    """Upload an in-memory blob."""
    client = get_minio_client()
    bio = io.BytesIO(data)
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=bio,
        length=len(data),
        content_type=content_type,
    )


def put_stream(
    bucket: str,
    object_name: str,
    stream: BinaryIO,
    length: int,
    content_type: str = "application/octet-stream",
) -> None:
    """Upload a file-like object whose total length is known."""
    client = get_minio_client()
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=stream,
        length=length,
        content_type=content_type,
    )


def remove(bucket: str, object_name: str) -> None:
    """Delete an object, swallowing not-found errors."""
    client = get_minio_client()
    try:
        client.remove_object(bucket, object_name)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject"}:
            return
        raise


def move(
    bucket: str,
    source: str,
    destination: str,
    content_type: str = "application/octet-stream",
) -> None:
    """Copy + delete. Used for trash/restore transitions."""
    client = get_minio_client()
    client.copy_object(
        bucket_name=bucket,
        object_name=destination,
        source=CopySource(bucket, source),
        metadata={"Content-Type": content_type},
    )
    client.remove_object(bucket, source)


def get_stream(bucket: str, object_name: str, chunk_size: int):
    """Yield raw bytes from an object for streaming downloads."""
    client = get_minio_client()
    response = client.get_object(bucket, object_name)
    try:
        while True:
            data = response.read(chunk_size)
            if not data:
                break
            yield data
    finally:
        response.close()
        response.release_conn()


def get_bytes(bucket: str, object_name: str, max_bytes: int | None = None) -> bytes:
    """Read an object's bytes into memory, optionally capped."""
    client = get_minio_client()
    response = client.get_object(bucket, object_name)
    try:
        if max_bytes is None:
            return response.read()
        return response.read(max_bytes)
    finally:
        response.close()
        response.release_conn()


def stat_size(bucket: str, object_name: str) -> int:
    """Return the stored object's size in bytes."""
    client = get_minio_client()
    obj = client.stat_object(bucket, object_name)
    return obj.size


def presigned_get_url(
    bucket: str,
    object_name: str,
    expires: Optional[timedelta] = None,
) -> str:
    """Generate a presigned GET URL with an explicit short expiry."""
    client = get_minio_client()
    return client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=expires or settings.presigned_url_expires,
    )

import boto3
from botocore.config import Config

from app.core.config import settings


def get_s3_client():
    """Create and return an S3 client."""
    kwargs = {
        "service_name": "s3",
        "region_name": settings.aws_region,
        "config": Config(signature_version="s3v4"),
    }
    if settings.aws_s3_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_s3_endpoint_url
    return boto3.client(**kwargs)


async def upload_file(s3_key: str, file_data: bytes, content_type: str) -> str:
    """Upload a file to S3 and return the S3 key."""
    client = get_s3_client()
    client.put_object(
        Bucket=settings.aws_s3_bucket,
        Key=s3_key,
        Body=file_data,
        ContentType=content_type,
    )
    return s3_key


async def delete_file(s3_key: str) -> None:
    """Delete a file from S3."""
    client = get_s3_client()
    client.delete_object(Bucket=settings.aws_s3_bucket, Key=s3_key)


async def delete_files(s3_keys: list[str]) -> None:
    """Delete multiple files from S3."""
    if not s3_keys:
        return
    client = get_s3_client()
    objects = [{"Key": key} for key in s3_keys]
    client.delete_objects(Bucket=settings.aws_s3_bucket, Delete={"Objects": objects})


def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for file access."""
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.aws_s3_bucket, "Key": s3_key},
        ExpiresIn=expires_in,
    )

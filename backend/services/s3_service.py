import boto3
from botocore.exceptions import NoCredentialsError
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)

s3_client = None

if settings.AWS_ACCESS_KEY_ID and settings.AWS_BUCKET_NAME:
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL,
        )
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")

async def upload_file_to_s3(file_obj, object_name: str) -> str | None:
    if not s3_client:
        return None
    
    try:
        s3_client.upload_fileobj(file_obj, settings.AWS_BUCKET_NAME, object_name)
        return f"s3://{settings.AWS_BUCKET_NAME}/{object_name}"
    except NoCredentialsError:
        logger.error("AWS credentials not available")
        return None
    except Exception as e:
        logger.error(f"Failed to upload to S3: {e}")
        return None

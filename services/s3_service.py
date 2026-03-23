import boto3
from botocore.exceptions import ClientError
from core.config import S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET, S3_PUBLIC_URL
import logging

logger = logging.getLogger(__name__)

# Initialize the S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name='us-east-1' # Default region, needed by boto3 even for MinIO
)

def upload_file_to_s3(file_obj, object_name: str, content_type: str = None) -> str:
    """
    Uploads a file object to S3 and returns the public URL.
    """
    extra_args = {}
    if content_type:
        extra_args['ContentType'] = content_type

    try:
        # Seek to beginning in case the file object was read elsewhere
        file_obj.seek(0)
        s3_client.upload_fileobj(
            file_obj,
            S3_BUCKET,
            object_name,
            ExtraArgs=extra_args
        )
        # Return the public URL
        return f"{S3_PUBLIC_URL}/{object_name}"
    except ClientError as e:
        logger.error(f"Failed to upload {object_name} to S3: {e}")
        raise

def delete_file_from_s3(object_name: str):
    """
    Deletes a file from S3 by its object name.
    """
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=object_name)
    except ClientError as e:
        logger.error(f"Failed to delete {object_name} from S3: {e}")
        # Don't strictly raise here, as failing to delete an old image shouldn't crash the app usually

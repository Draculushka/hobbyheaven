import logging

import boto3
from botocore.exceptions import ClientError

from core.config import CDN_URL, S3_ACCESS_KEY, S3_BUCKET, S3_ENDPOINT, S3_PUBLIC_URL, S3_SECRET_KEY

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
    Uploads a file object to S3 and returns the public URL (optionally via CDN).
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

        # Determine the public URL (direct S3 or CDN)
        if CDN_URL:
            # If CDN_URL is set, we assume it serves the bucket directly
            return f"{CDN_URL.rstrip('/')}/{object_name}"
        else:
            # Fallback to direct S3 URL
            return f"{S3_PUBLIC_URL.rstrip('/')}/{object_name}"
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

def init_s3_bucket():
    """
    Initializes the S3 bucket if it doesn't exist and sets a public-read policy.
    This ensures that images uploaded to MinIO can be loaded by the browser directly.
    """
    try:
        try:
            s3_client.head_bucket(Bucket=S3_BUCKET)
            logger.info(f"S3 Bucket '{S3_BUCKET}' already exists.")
        except ClientError:
            logger.info(f"S3 Bucket '{S3_BUCKET}' not found. Creating it...")
            s3_client.create_bucket(Bucket=S3_BUCKET)

        # Set bucket policy to allow public read access to all objects
        import json
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{S3_BUCKET}/*"]
                }
            ]
        }
        s3_client.put_bucket_policy(Bucket=S3_BUCKET, Policy=json.dumps(policy))
        logger.info(f"Public read policy applied to bucket '{S3_BUCKET}'.")
    except Exception as e:
        logger.error(f"Error initializing S3 bucket: {e}")

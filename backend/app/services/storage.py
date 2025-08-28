"""
Cloudflare R2 storage service
"""

import boto3
import logging
from typing import Tuple, Dict
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    """Service for interacting with Cloudflare R2 storage"""
    
    def __init__(self):
        """Initialize R2 client"""
        self.client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name='auto'  # Cloudflare R2 uses 'auto'
        )
        self.bucket_name = settings.R2_BUCKET_NAME
    
    async def generate_presigned_upload_url(
        self, 
        key: str, 
        content_type: str,
        expires_in: int = 3600
    ) -> Tuple[str, Dict[str, str]]:
        """Generate presigned URL for uploading to R2"""
        try:
            # Generate presigned POST URL
            response = self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=key,
                Fields={
                    'Content-Type': content_type
                },
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, settings.MAX_UPLOAD_SIZE]
                ],
                ExpiresIn=expires_in
            )
            
            # Extract URL and required headers/fields
            upload_url = response['url']
            headers = {
                'Content-Type': content_type,
                **response['fields']
            }
            
            return upload_url, headers
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {key}: {e}")
            raise Exception(f"Failed to generate presigned URL: {e}")
    
    async def generate_presigned_download_url(
        self, 
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate presigned URL for downloading from R2"""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expires_in
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate download URL for {key}: {e}")
            raise Exception(f"Failed to generate download URL: {e}")
    
    async def delete_object(self, key: str) -> bool:
        """Delete an object from R2"""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete object {key}: {e}")
            return False
    
    async def delete_objects(self, keys: list) -> Dict[str, bool]:
        """Delete multiple objects from R2"""
        results = {}
        
        for key in keys:
            results[key] = await self.delete_object(key)
        
        return results
    
    async def upload_object(
        self, 
        key: str, 
        data: bytes, 
        content_type: str,
        metadata: Dict[str, str] = None
    ) -> bool:
        """Upload an object directly to R2"""
        try:
            extra_args = {'ContentType': content_type}
            if metadata:
                extra_args['Metadata'] = metadata
                
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                **extra_args
            )
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload object {key}: {e}")
            return False
    
    def get_public_url(self, key: str) -> str:
        """Get public URL for an object (if bucket is public)"""
        return f"{settings.R2_PUBLIC_URL}/{key}"
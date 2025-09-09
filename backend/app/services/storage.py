"""
Cloudflare R2 storage service
"""

import boto3
import logging
import base64
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
    
    async def download_object(self, key: str) -> bytes:
        """Download an object from R2"""
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Failed to download object {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading object {key}: {e}")
            return None
    
    def get_public_url(self, key: str) -> str:
        """Get public URL for an object (if bucket is public)"""
        return f"{settings.R2_PUBLIC_URL}/{key}"
    
    async def upload_base64_image(
        self, 
        key: str, 
        base64_data: str, 
        content_type: str = "image/png",
        metadata: Dict[str, str] = None
    ) -> bool:
        """Upload a base64-encoded image to R2"""
        try:
            # Decode base64 data
            image_data = base64.b64decode(base64_data)
            
            # Upload to R2
            success = await self.upload_object(key, image_data, content_type, metadata)
            
            if success:
                logger.info(f"Successfully uploaded {key} to R2")
            else:
                logger.error(f"Failed to upload {key} to R2")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to upload base64 image {key}: {e}")
            return False
    
    async def upload_scene_files(
        self, 
        scene_id: str, 
        thumbnail_base64: str = None,
        depth_base64: str = None
    ) -> Dict[str, str]:
        """Upload scene-related files (thumbnail, depth map) to R2"""
        uploaded_keys = {}
        
        try:
            # Upload thumbnail if provided
            if thumbnail_base64:
                thumb_key = f"scenes/{scene_id}/thumbnail.jpg"
                success = await self.upload_base64_image(
                    thumb_key, thumbnail_base64, "image/jpeg",
                    {"scene_id": scene_id, "type": "thumbnail"}
                )
                if success:
                    uploaded_keys["r2_key_thumbnail"] = thumb_key  # Match database schema
            
            # Upload depth map if provided
            if depth_base64:
                depth_key = f"scenes/{scene_id}/depth.png"
                success = await self.upload_base64_image(
                    depth_key, depth_base64, "image/png",
                    {"scene_id": scene_id, "type": "depth_map"}
                )
                if success:
                    uploaded_keys["r2_key_depth"] = depth_key  # Match database schema
            
            return uploaded_keys
            
        except Exception as e:
            logger.error(f"Failed to upload scene files for {scene_id}: {e}")
            return uploaded_keys
    
    async def upload_object_masks(
        self, 
        scene_id: str, 
        objects_with_masks: list
    ) -> Dict[str, str]:
        """Upload object mask files to R2"""
        uploaded_keys = {}
        
        try:
            for i, obj in enumerate(objects_with_masks):
                if obj.get("has_mask") and obj.get("mask_base64"):
                    # Generate mask key
                    object_label = obj.get("label", "object").replace(" ", "_").lower()
                    mask_key = f"scenes/{scene_id}/masks/{i}_{object_label}_mask.png"
                    
                    success = await self.upload_base64_image(
                        mask_key, obj["mask_base64"], "image/png",
                        {
                            "scene_id": scene_id, 
                            "object_index": str(i),
                            "object_label": object_label,
                            "type": "segmentation_mask"
                        }
                    )
                    
                    if success:
                        # Store the key for this object (using object index as identifier)
                        uploaded_keys[f"object_{i}_mask_key"] = mask_key
            
            return uploaded_keys
            
        except Exception as e:
            logger.error(f"Failed to upload object masks for {scene_id}: {e}")
            return uploaded_keys
    
    async def upload_object_thumbnails(
        self, 
        scene_id: str, 
        objects_with_thumbnails: list
    ) -> Dict[str, str]:
        """Upload object thumbnail files to R2"""
        uploaded_keys = {}
        
        try:
            for i, obj in enumerate(objects_with_thumbnails):
                if obj.get("thumb_base64"):
                    # Generate thumbnail key
                    object_label = obj.get("label", "object").replace(" ", "_").lower()
                    thumb_key = f"scenes/{scene_id}/thumbs/{i}_{object_label}_thumb.jpg"
                    
                    success = await self.upload_base64_image(
                        thumb_key, obj["thumb_base64"], "image/jpeg",
                        {
                            "scene_id": scene_id,
                            "object_index": str(i),
                            "object_label": object_label, 
                            "type": "object_thumbnail"
                        }
                    )
                    
                    if success:
                        # Store the key for this object (using object index as identifier)
                        uploaded_keys[f"object_{i}_thumb_key"] = thumb_key
            
            return uploaded_keys
            
        except Exception as e:
            logger.error(f"Failed to upload object thumbnails for {scene_id}: {e}")
            return uploaded_keys
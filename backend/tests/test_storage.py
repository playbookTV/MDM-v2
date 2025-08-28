"""
Test cases for storage service functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from botocore.exceptions import ClientError
from app.services.storage import StorageService
from app.core.config import settings


class TestStorageService:
    """Test StorageService functionality"""
    
    @pytest.fixture
    def storage_service(self):
        """Create StorageService instance with mocked boto3 client"""
        with patch('app.services.storage.boto3.client') as mock_boto3:
            service = StorageService()
            service.client = mock_boto3.return_value
            return service, mock_boto3.return_value
    
    @pytest.mark.asyncio
    async def test_upload_object_success(self, storage_service):
        """Test successful object upload"""
        service, mock_client = storage_service
        
        # Mock successful put_object
        mock_client.put_object.return_value = {}
        
        # Test data
        test_data = b"test image data"
        test_key = "test/image.jpg"
        content_type = "image/jpeg"
        metadata = {"source": "test"}
        
        # Execute upload
        result = await service.upload_object(test_key, test_data, content_type, metadata)
        
        # Verify success
        assert result is True
        mock_client.put_object.assert_called_once_with(
            Bucket=settings.R2_BUCKET_NAME,
            Key=test_key,
            Body=test_data,
            ContentType=content_type,
            Metadata=metadata
        )
    
    @pytest.mark.asyncio
    async def test_upload_object_failure(self, storage_service):
        """Test object upload failure handling"""
        service, mock_client = storage_service
        
        # Mock ClientError
        mock_client.put_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
            operation_name='PutObject'
        )
        
        # Test data
        test_data = b"test image data"
        test_key = "test/image.jpg"
        content_type = "image/jpeg"
        
        # Execute upload
        result = await service.upload_object(test_key, test_data, content_type)
        
        # Verify failure handling
        assert result is False
    
    @pytest.mark.asyncio
    async def test_upload_object_without_metadata(self, storage_service):
        """Test object upload without metadata"""
        service, mock_client = storage_service
        
        # Mock successful put_object
        mock_client.put_object.return_value = {}
        
        # Test data without metadata
        test_data = b"test image data"
        test_key = "test/image.jpg"
        content_type = "image/jpeg"
        
        # Execute upload
        result = await service.upload_object(test_key, test_data, content_type)
        
        # Verify success and correct call
        assert result is True
        mock_client.put_object.assert_called_once_with(
            Bucket=settings.R2_BUCKET_NAME,
            Key=test_key,
            Body=test_data,
            ContentType=content_type
        )
    
    @pytest.mark.asyncio
    async def test_generate_presigned_upload_url_success(self, storage_service):
        """Test successful presigned upload URL generation"""
        service, mock_client = storage_service
        
        # Mock successful generate_presigned_post
        mock_response = {
            'url': 'https://bucket.r2.cloudflarestorage.com',
            'fields': {
                'key': 'test/image.jpg',
                'AWSAccessKeyId': 'test-key',
                'policy': 'test-policy',
                'signature': 'test-signature'
            }
        }
        mock_client.generate_presigned_post.return_value = mock_response
        
        # Execute generation
        test_key = "test/image.jpg"
        content_type = "image/jpeg"
        
        upload_url, headers = await service.generate_presigned_upload_url(test_key, content_type)
        
        # Verify results
        assert upload_url == mock_response['url']
        assert 'Content-Type' in headers
        assert headers['Content-Type'] == content_type
        assert 'key' in headers
        
        # Verify client was called correctly
        mock_client.generate_presigned_post.assert_called_once()
        call_args = mock_client.generate_presigned_post.call_args
        assert call_args[1]['Bucket'] == settings.R2_BUCKET_NAME
        assert call_args[1]['Key'] == test_key
    
    @pytest.mark.asyncio
    async def test_generate_presigned_upload_url_failure(self, storage_service):
        """Test presigned upload URL generation failure"""
        service, mock_client = storage_service
        
        # Mock ClientError
        mock_client.generate_presigned_post.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='GeneratePresignedPost'
        )
        
        # Execute generation and expect exception
        with pytest.raises(Exception) as exc_info:
            await service.generate_presigned_upload_url("test/image.jpg", "image/jpeg")
        
        assert "Failed to generate presigned URL" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_presigned_download_url_success(self, storage_service):
        """Test successful presigned download URL generation"""
        service, mock_client = storage_service
        
        # Mock successful generate_presigned_url
        expected_url = "https://bucket.r2.cloudflarestorage.com/test/image.jpg?signature=test"
        mock_client.generate_presigned_url.return_value = expected_url
        
        # Execute generation
        test_key = "test/image.jpg"
        
        download_url = await service.generate_presigned_download_url(test_key)
        
        # Verify results
        assert download_url == expected_url
        mock_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': settings.R2_BUCKET_NAME, 'Key': test_key},
            ExpiresIn=3600
        )
    
    @pytest.mark.asyncio
    async def test_delete_object_success(self, storage_service):
        """Test successful object deletion"""
        service, mock_client = storage_service
        
        # Mock successful delete_object
        mock_client.delete_object.return_value = {}
        
        # Execute deletion
        test_key = "test/image.jpg"
        result = await service.delete_object(test_key)
        
        # Verify success
        assert result is True
        mock_client.delete_object.assert_called_once_with(
            Bucket=settings.R2_BUCKET_NAME,
            Key=test_key
        )
    
    @pytest.mark.asyncio
    async def test_delete_object_failure(self, storage_service):
        """Test object deletion failure handling"""
        service, mock_client = storage_service
        
        # Mock ClientError
        mock_client.delete_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
            operation_name='DeleteObject'
        )
        
        # Execute deletion
        test_key = "test/image.jpg"
        result = await service.delete_object(test_key)
        
        # Verify failure handling
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_objects_batch(self, storage_service):
        """Test batch object deletion"""
        service, mock_client = storage_service
        
        # Mock successful and failed deletions
        mock_client.delete_object.side_effect = [
            {},  # Success for first key
            ClientError(
                error_response={'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
                operation_name='DeleteObject'
            )  # Failure for second key
        ]
        
        # Execute batch deletion
        test_keys = ["test/image1.jpg", "test/image2.jpg"]
        results = await service.delete_objects(test_keys)
        
        # Verify mixed results
        assert len(results) == 2
        assert results["test/image1.jpg"] is True
        assert results["test/image2.jpg"] is False
        assert mock_client.delete_object.call_count == 2
    
    def test_get_public_url(self, storage_service):
        """Test public URL generation"""
        service, _ = storage_service
        
        # Test URL generation
        test_key = "test/image.jpg"
        public_url = service.get_public_url(test_key)
        
        # Verify URL format
        expected_url = f"{settings.R2_PUBLIC_URL}/{test_key}"
        assert public_url == expected_url
    
    @pytest.mark.asyncio
    async def test_upload_object_with_custom_expiry(self, storage_service):
        """Test presigned URL generation with custom expiry"""
        service, mock_client = storage_service
        
        # Mock response
        mock_response = {
            'url': 'https://bucket.r2.cloudflarestorage.com',
            'fields': {'key': 'test/image.jpg'}
        }
        mock_client.generate_presigned_post.return_value = mock_response
        
        # Execute with custom expiry
        test_key = "test/image.jpg"
        content_type = "image/jpeg"
        custom_expiry = 7200  # 2 hours
        
        await service.generate_presigned_upload_url(test_key, content_type, custom_expiry)
        
        # Verify custom expiry was used
        call_args = mock_client.generate_presigned_post.call_args
        assert call_args[1]['ExpiresIn'] == custom_expiry
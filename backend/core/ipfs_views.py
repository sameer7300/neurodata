"""
API views for IPFS dataset storage operations.
"""
import logging
import os
import tempfile
from typing import Dict, Any

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpResponse, Http404
from django.utils import timezone

from .ipfs_service import ipfs_service
from .ipfs_providers import test_provider_connection
from core.utils import create_response_data
from apps.datasets.models import Dataset

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_dataset(request):
    """
    Upload dataset to IPFS with encryption.
    """
    try:
        dataset_id = request.data.get('dataset_id')
        file = request.FILES.get('file')
        encrypt = request.data.get('encrypt', 'true').lower() == 'true'
        
        if not dataset_id:
            return Response(
                create_response_data(
                    success=False,
                    message="Dataset ID is required",
                    errors={'dataset_id': 'This field is required'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not file:
            return Response(
                create_response_data(
                    success=False,
                    message="File is required",
                    errors={'file': 'This field is required'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify dataset ownership
        try:
            dataset = Dataset.objects.get(id=dataset_id, owner=request.user)
        except Dataset.DoesNotExist:
            return Response(
                create_response_data(
                    success=False,
                    message="Dataset not found or access denied",
                    errors={'dataset': 'Dataset not found or you do not have permission'}
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # Upload to IPFS
            upload_result = ipfs_service.upload_dataset(
                file_path=temp_file_path,
                dataset_id=int(dataset_id),
                owner_id=request.user.id,
                encrypt=encrypt
            )
            
            if upload_result.success:
                # Update dataset with IPFS hash
                dataset.ipfs_hash = upload_result.ipfs_hash
                dataset.file_size = upload_result.size
                dataset.is_encrypted = encrypt
                dataset.save()
                
                return Response(
                    create_response_data(
                        success=True,
                        message="Dataset uploaded successfully",
                        data={
                            'ipfs_hash': upload_result.ipfs_hash,
                            'ipfs_url': upload_result.ipfs_url,
                            'size': upload_result.size,
                            'encrypted': encrypt,
                            'dataset_id': dataset_id
                        }
                    )
                )
            else:
                return Response(
                    create_response_data(
                        success=False,
                        message="Upload failed",
                        errors={'upload': upload_result.error}
                    ),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error uploading dataset: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Upload failed",
                errors={'server': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_dataset(request, dataset_id):
    """
    Download dataset from IPFS with decryption.
    """
    try:
        # Get dataset
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist:
            raise Http404("Dataset not found")
        
        # Check access permissions (owner or purchased)
        has_access = (
            dataset.owner == request.user or
            dataset.price == 0 or  # Free datasets
            dataset.purchases.filter(
                buyer=request.user,
                status__in=['completed', 'in_escrow']
            ).exists()
        )
        
        if not has_access:
            return Response(
                create_response_data(
                    success=False,
                    message="Access denied",
                    errors={'access': 'You do not have permission to download this dataset'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Download from IPFS
        success, data, error = ipfs_service.download_dataset(
            dataset_id=dataset_id,
            user_id=request.user.id,
            ipfs_hash=dataset.ipfs_hash
        )
        
        if not success:
            return Response(
                create_response_data(
                    success=False,
                    message="Download failed",
                    errors={'download': error}
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return file as HTTP response
        response = HttpResponse(
            data,
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{dataset.title}.{dataset.file_type}"'
        response['Content-Length'] = len(data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading dataset: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Download failed",
                errors={'server': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dataset_info(request, dataset_id):
    """
    Get IPFS information for a dataset.
    """
    try:
        # Verify dataset access
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist:
            return Response(
                create_response_data(
                    success=False,
                    message="Dataset not found",
                    errors={'dataset': 'Dataset not found'}
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check basic access (at least view permission)
        has_access = (
            dataset.owner == request.user or
            dataset.price == 0 or
            dataset.purchases.filter(buyer=request.user).exists()
        )
        
        if not has_access:
            return Response(
                create_response_data(
                    success=False,
                    message="Access denied",
                    errors={'access': 'You do not have permission to view this dataset info'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get IPFS info
        ipfs_info = ipfs_service.get_dataset_info(dataset_id)
        
        if 'error' in ipfs_info:
            return Response(
                create_response_data(
                    success=False,
                    message="Failed to get dataset info",
                    errors={'ipfs': ipfs_info['error']}
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            create_response_data(
                success=True,
                data=ipfs_info
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting dataset info: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to get dataset info",
                errors={'server': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_integrity(request, dataset_id):
    """
    Verify dataset integrity.
    """
    try:
        # Verify dataset ownership or purchase
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist:
            return Response(
                create_response_data(
                    success=False,
                    message="Dataset not found",
                    errors={'dataset': 'Dataset not found'}
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        has_access = (
            dataset.owner == request.user or
            dataset.purchases.filter(
                buyer=request.user,
                status__in=['completed', 'in_escrow']
            ).exists()
        )
        
        if not has_access:
            return Response(
                create_response_data(
                    success=False,
                    message="Access denied",
                    errors={'access': 'You do not have permission to verify this dataset'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify integrity
        expected_hash = request.data.get('expected_hash')
        is_valid = ipfs_service.verify_integrity(dataset_id, expected_hash)
        
        return Response(
            create_response_data(
                success=True,
                data={
                    'dataset_id': dataset_id,
                    'integrity_valid': is_valid,
                    'verified_at': timezone.now().isoformat()
                }
            )
        )
        
    except Exception as e:
        logger.error(f"Error verifying integrity: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Integrity verification failed",
                errors={'server': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ipfs_status(request):
    """
    Get IPFS service status and configuration.
    """
    try:
        # Only allow staff users to see detailed status
        if not request.user.is_staff:
            return Response(
                create_response_data(
                    success=False,
                    message="Admin access required",
                    errors={'permission': 'Admin access required'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Test provider connection
        from django.conf import settings
        ipfs_config = getattr(settings, 'IPFS_CONFIG', {})
        provider_type = ipfs_config.get('PROVIDER', 'pinata')
        
        connection_test = test_provider_connection(provider_type, ipfs_config)
        
        status_info = {
            'provider': provider_type,
            'encryption_enabled': ipfs_config.get('ENCRYPTION_ENABLED', True),
            'connection_test': connection_test,
            'gateway_url': ipfs_service.gateway_url,
            'cache_timeout': ipfs_service.cache_timeout
        }
        
        return Response(
            create_response_data(
                success=True,
                data=status_info
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting IPFS status: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to get IPFS status",
                errors={'server': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_connection(request):
    """
    Test IPFS provider connection.
    """
    try:
        if not request.user.is_staff:
            return Response(
                create_response_data(
                    success=False,
                    message="Admin access required",
                    errors={'permission': 'Admin access required'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        provider_type = request.data.get('provider', 'pinata')
        config = request.data.get('config', {})
        
        # Use current config if not provided
        if not config:
            from django.conf import settings
            config = getattr(settings, 'IPFS_CONFIG', {})
        
        test_result = test_provider_connection(provider_type, config)
        
        return Response(
            create_response_data(
                success=test_result['success'],
                message=test_result.get('message', 'Connection test completed'),
                data=test_result
            )
        )
        
    except Exception as e:
        logger.error(f"Error testing IPFS connection: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Connection test failed",
                errors={'server': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_datasets_ipfs(request):
    """
    Get IPFS information for user's datasets.
    """
    try:
        # Get user's datasets
        datasets = Dataset.objects.filter(owner=request.user)
        
        dataset_info = []
        for dataset in datasets:
            ipfs_info = ipfs_service.get_dataset_info(dataset.id)
            
            dataset_data = {
                'dataset_id': dataset.id,
                'title': dataset.title,
                'file_type': dataset.file_type,
                'price': str(dataset.price),
                'created_at': dataset.created_at.isoformat(),
                'ipfs_info': ipfs_info
            }
            
            dataset_info.append(dataset_data)
        
        return Response(
            create_response_data(
                success=True,
                data={
                    'datasets': dataset_info,
                    'total_count': len(dataset_info)
                }
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting user datasets IPFS info: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to get datasets info",
                errors={'server': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

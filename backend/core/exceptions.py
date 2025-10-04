"""
Custom exceptions for NeuroData project.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class NeuroDataException(Exception):
    """Base exception class for NeuroData."""
    pass


class BlockchainException(NeuroDataException):
    """Exception raised for blockchain-related errors."""
    pass


class IPFSException(NeuroDataException):
    """Exception raised for IPFS-related errors."""
    pass


class DatasetException(NeuroDataException):
    """Exception raised for dataset-related errors."""
    pass


class MLTrainingException(NeuroDataException):
    """Exception raised for ML training-related errors."""
    pass


class InsufficientFundsException(NeuroDataException):
    """Exception raised when user has insufficient funds."""
    pass


class DatasetNotAccessibleException(NeuroDataException):
    """Exception raised when user doesn't have access to dataset."""
    pass


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status_code': response.status_code
        }
        
        # Log the exception
        logger.error(f"API Exception: {exc}", extra={
            'request': context.get('request'),
            'view': context.get('view'),
            'status_code': response.status_code
        })
        
        response.data = custom_response_data
    
    # Handle custom exceptions
    elif isinstance(exc, BlockchainException):
        custom_response_data = {
            'error': True,
            'message': 'Blockchain operation failed',
            'details': str(exc),
            'status_code': status.HTTP_503_SERVICE_UNAVAILABLE
        }
        logger.error(f"Blockchain Exception: {exc}")
        response = Response(custom_response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    elif isinstance(exc, IPFSException):
        custom_response_data = {
            'error': True,
            'message': 'Storage operation failed',
            'details': str(exc),
            'status_code': status.HTTP_503_SERVICE_UNAVAILABLE
        }
        logger.error(f"IPFS Exception: {exc}")
        response = Response(custom_response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    elif isinstance(exc, DatasetException):
        custom_response_data = {
            'error': True,
            'message': 'Dataset operation failed',
            'details': str(exc),
            'status_code': status.HTTP_400_BAD_REQUEST
        }
        logger.error(f"Dataset Exception: {exc}")
        response = Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    elif isinstance(exc, InsufficientFundsException):
        custom_response_data = {
            'error': True,
            'message': 'Insufficient funds',
            'details': str(exc),
            'status_code': status.HTTP_402_PAYMENT_REQUIRED
        }
        logger.warning(f"Insufficient Funds Exception: {exc}")
        response = Response(custom_response_data, status=status.HTTP_402_PAYMENT_REQUIRED)
    
    elif isinstance(exc, DatasetNotAccessibleException):
        custom_response_data = {
            'error': True,
            'message': 'Dataset not accessible',
            'details': str(exc),
            'status_code': status.HTTP_403_FORBIDDEN
        }
        logger.warning(f"Dataset Access Exception: {exc}")
        response = Response(custom_response_data, status=status.HTTP_403_FORBIDDEN)
    
    return response

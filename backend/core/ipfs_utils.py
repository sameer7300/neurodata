"""
IPFS utility functions and helpers.
"""
import hashlib
import logging
import mimetypes
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class IPFSUtils:
    """
    Collection of IPFS utility functions.
    """
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calculate hash of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm ('sha256', 'md5', 'sha1')
            
        Returns:
            Hex digest of the file hash
        """
        try:
            hash_func = getattr(hashlib, algorithm)()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating file hash: {str(e)}")
            return ""
    
    @staticmethod
    def calculate_data_hash(data: bytes, algorithm: str = 'sha256') -> str:
        """
        Calculate hash of data.
        
        Args:
            data: Data bytes
            algorithm: Hash algorithm
            
        Returns:
            Hex digest of the data hash
        """
        try:
            hash_func = getattr(hashlib, algorithm)()
            hash_func.update(data)
            return hash_func.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating data hash: {str(e)}")
            return ""
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            if not os.path.exists(file_path):
                return {'error': 'File not found'}
            
            stat = os.stat(file_path)
            
            # Get MIME type
            mime_type, encoding = mimetypes.guess_type(file_path)
            
            # Calculate hashes
            sha256_hash = IPFSUtils.calculate_file_hash(file_path, 'sha256')
            md5_hash = IPFSUtils.calculate_file_hash(file_path, 'md5')
            
            return {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': stat.st_size,
                'mime_type': mime_type,
                'encoding': encoding,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'sha256_hash': sha256_hash,
                'md5_hash': md5_hash,
                'is_readable': os.access(file_path, os.R_OK),
                'file_extension': os.path.splitext(file_path)[1].lower()
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def validate_file_type(file_path: str, allowed_types: List[str] = None) -> Tuple[bool, str]:
        """
        Validate file type against allowed types.
        
        Args:
            file_path: Path to the file
            allowed_types: List of allowed file extensions (e.g., ['.csv', '.json'])
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if allowed_types is None:
                # Default allowed types for datasets
                allowed_types = [
                    '.csv', '.json', '.xlsx', '.xls', '.parquet',
                    '.txt', '.tsv', '.xml', '.yaml', '.yml',
                    '.h5', '.hdf5', '.pkl', '.pickle', '.npz'
                ]
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension in allowed_types:
                return True, ""
            else:
                return False, f"File type {file_extension} is not allowed. Allowed types: {', '.join(allowed_types)}"
                
        except Exception as e:
            logger.error(f"Error validating file type: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def validate_file_size(file_path: str, max_size_mb: int = None) -> Tuple[bool, str]:
        """
        Validate file size against maximum allowed size.
        
        Args:
            file_path: Path to the file
            max_size_mb: Maximum size in MB
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if max_size_mb is None:
                max_size_mb = getattr(settings, 'MAX_DATASET_SIZE_MB', 500)  # 500MB default
            
            if not os.path.exists(file_path):
                return False, "File not found"
            
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if file_size <= max_size_bytes:
                return True, ""
            else:
                actual_size_mb = file_size / (1024 * 1024)
                return False, f"File size ({actual_size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
                
        except Exception as e:
            logger.error(f"Error validating file size: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        try:
            if size_bytes == 0:
                return "0 B"
            
            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            size = float(size_bytes)
            
            while size >= 1024.0 and i < len(size_names) - 1:
                size /= 1024.0
                i += 1
            
            return f"{size:.2f} {size_names[i]}"
            
        except Exception as e:
            logger.error(f"Error formatting file size: {str(e)}")
            return f"{size_bytes} B"
    
    @staticmethod
    def is_ipfs_hash_valid(ipfs_hash: str) -> bool:
        """
        Validate IPFS hash format.
        
        Args:
            ipfs_hash: IPFS hash to validate
            
        Returns:
            True if valid IPFS hash format
        """
        try:
            if not ipfs_hash or not isinstance(ipfs_hash, str):
                return False
            
            # Basic IPFS hash validation
            # CIDv0: starts with 'Qm' and is 46 characters long
            # CIDv1: starts with 'b' or other multibase prefix
            
            if ipfs_hash.startswith('Qm') and len(ipfs_hash) == 46:
                # CIDv0 format
                return all(c in '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz' for c in ipfs_hash[2:])
            elif len(ipfs_hash) > 10:  # CIDv1 format (more flexible)
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error validating IPFS hash: {str(e)}")
            return False
    
    @staticmethod
    def get_ipfs_gateway_url(ipfs_hash: str, gateway_url: str = None) -> str:
        """
        Get IPFS gateway URL for a hash.
        
        Args:
            ipfs_hash: IPFS hash
            gateway_url: Custom gateway URL
            
        Returns:
            Full gateway URL
        """
        try:
            if not IPFSUtils.is_ipfs_hash_valid(ipfs_hash):
                return ""
            
            if gateway_url is None:
                # Use default gateway from settings
                ipfs_config = getattr(settings, 'IPFS_CONFIG', {})
                provider = ipfs_config.get('PROVIDER', 'pinata')
                
                if provider == 'pinata':
                    gateway_url = "https://gateway.pinata.cloud/ipfs/"
                elif provider == 'web3_storage':
                    gateway_url = "https://w3s.link/ipfs/"
                elif provider == 'infura':
                    gateway_url = "https://ipfs.infura.io/ipfs/"
                else:
                    gateway_url = "https://ipfs.io/ipfs/"
            
            return f"{gateway_url.rstrip('/')}/{ipfs_hash}"
            
        except Exception as e:
            logger.error(f"Error getting gateway URL: {str(e)}")
            return ""
    
    @staticmethod
    def estimate_upload_time(file_size_bytes: int, connection_speed_mbps: float = 10.0) -> Dict[str, Any]:
        """
        Estimate upload time based on file size and connection speed.
        
        Args:
            file_size_bytes: File size in bytes
            connection_speed_mbps: Connection speed in Mbps
            
        Returns:
            Dictionary with time estimates
        """
        try:
            # Convert to bits and account for overhead
            file_size_bits = file_size_bytes * 8
            connection_speed_bps = connection_speed_mbps * 1_000_000 * 0.8  # 80% efficiency
            
            # Calculate time in seconds
            upload_time_seconds = file_size_bits / connection_speed_bps
            
            # Add processing overhead (encryption, IPFS processing)
            processing_overhead = min(30, file_size_bytes / (1024 * 1024))  # Max 30 seconds
            total_time_seconds = upload_time_seconds + processing_overhead
            
            return {
                'file_size_mb': file_size_bytes / (1024 * 1024),
                'connection_speed_mbps': connection_speed_mbps,
                'upload_time_seconds': upload_time_seconds,
                'processing_overhead_seconds': processing_overhead,
                'total_time_seconds': total_time_seconds,
                'estimated_time_formatted': IPFSUtils.format_duration(total_time_seconds)
            }
            
        except Exception as e:
            logger.error(f"Error estimating upload time: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        try:
            if seconds < 60:
                return f"{seconds:.1f} seconds"
            elif seconds < 3600:
                minutes = seconds / 60
                return f"{minutes:.1f} minutes"
            else:
                hours = seconds / 3600
                return f"{hours:.1f} hours"
                
        except Exception as e:
            logger.error(f"Error formatting duration: {str(e)}")
            return f"{seconds} seconds"
    
    @staticmethod
    def get_dataset_storage_stats() -> Dict[str, Any]:
        """
        Get storage statistics for all datasets.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            from apps.datasets.models import Dataset
            
            # Get all datasets with IPFS hashes
            datasets = Dataset.objects.exclude(ipfs_hash__isnull=True).exclude(ipfs_hash='')
            
            total_datasets = datasets.count()
            total_size = sum(dataset.file_size or 0 for dataset in datasets)
            encrypted_count = datasets.filter(is_encrypted=True).count()
            
            # Group by file type
            file_types = {}
            for dataset in datasets:
                file_type = dataset.file_type or 'unknown'
                if file_type not in file_types:
                    file_types[file_type] = {'count': 0, 'size': 0}
                file_types[file_type]['count'] += 1
                file_types[file_type]['size'] += dataset.file_size or 0
            
            # Recent uploads (last 30 days)
            recent_date = timezone.now() - timedelta(days=30)
            recent_uploads = datasets.filter(created_at__gte=recent_date).count()
            
            return {
                'total_datasets': total_datasets,
                'total_size_bytes': total_size,
                'total_size_formatted': IPFSUtils.format_file_size(total_size),
                'encrypted_datasets': encrypted_count,
                'encryption_percentage': (encrypted_count / total_datasets * 100) if total_datasets > 0 else 0,
                'file_types': file_types,
                'recent_uploads_30_days': recent_uploads,
                'average_file_size': total_size / total_datasets if total_datasets > 0 else 0,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def cleanup_temp_files(temp_dir: str = None, max_age_hours: int = 24):
        """
        Clean up temporary files older than specified age.
        
        Args:
            temp_dir: Temporary directory path
            max_age_hours: Maximum age in hours
        """
        try:
            if temp_dir is None:
                temp_dir = getattr(settings, 'TEMP_DIR', '/tmp')
            
            if not os.path.exists(temp_dir):
                return
            
            cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
            cutoff_timestamp = cutoff_time.timestamp()
            
            cleaned_count = 0
            cleaned_size = 0
            
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                
                try:
                    if os.path.isfile(file_path):
                        file_mtime = os.path.getmtime(file_path)
                        
                        if file_mtime < cutoff_timestamp:
                            file_size = os.path.getsize(file_path)
                            os.unlink(file_path)
                            cleaned_count += 1
                            cleaned_size += file_size
                            
                except Exception as e:
                    logger.warning(f"Error cleaning temp file {file_path}: {str(e)}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} temp files, freed {IPFSUtils.format_file_size(cleaned_size)}")
                
        except Exception as e:
            logger.error(f"Error cleaning temp files: {str(e)}")


def validate_dataset_file(file_path: str) -> Dict[str, Any]:
    """
    Comprehensive dataset file validation.
    
    Args:
        file_path: Path to the dataset file
        
    Returns:
        Validation result dictionary
    """
    try:
        # Get file info
        file_info = IPFSUtils.get_file_info(file_path)
        if 'error' in file_info:
            return {'valid': False, 'errors': [file_info['error']]}
        
        errors = []
        warnings = []
        
        # Validate file type
        is_valid_type, type_error = IPFSUtils.validate_file_type(file_path)
        if not is_valid_type:
            errors.append(type_error)
        
        # Validate file size
        is_valid_size, size_error = IPFSUtils.validate_file_size(file_path)
        if not is_valid_size:
            errors.append(size_error)
        
        # Check if file is readable
        if not file_info['is_readable']:
            errors.append("File is not readable")
        
        # Check for empty file
        if file_info['file_size'] == 0:
            errors.append("File is empty")
        
        # Warnings for large files
        if file_info['file_size'] > 100 * 1024 * 1024:  # 100MB
            warnings.append("Large file detected - upload may take longer")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'file_info': file_info,
            'upload_estimate': IPFSUtils.estimate_upload_time(file_info['file_size'])
        }
        
    except Exception as e:
        logger.error(f"Error validating dataset file: {str(e)}")
        return {
            'valid': False,
            'errors': [str(e)],
            'warnings': [],
            'file_info': None
        }


def get_ipfs_health_check() -> Dict[str, Any]:
    """
    Perform IPFS service health check.
    
    Returns:
        Health check result dictionary
    """
    try:
        from .ipfs_service import ipfs_service
        from .ipfs_providers import test_provider_connection
        from django.conf import settings
        
        ipfs_config = getattr(settings, 'IPFS_CONFIG', {})
        provider_type = ipfs_config.get('PROVIDER', 'pinata')
        
        # Test connection
        connection_test = test_provider_connection(provider_type, ipfs_config)
        
        # Get storage stats
        storage_stats = IPFSUtils.get_dataset_storage_stats()
        
        # Check cache health
        cache_test_key = 'ipfs_health_check_test'
        cache_test_value = 'test_value'
        cache.set(cache_test_key, cache_test_value, timeout=60)
        cache_working = cache.get(cache_test_key) == cache_test_value
        cache.delete(cache_test_key)
        
        return {
            'overall_health': 'healthy' if connection_test['success'] and cache_working else 'unhealthy',
            'provider': provider_type,
            'connection_test': connection_test,
            'cache_working': cache_working,
            'storage_stats': storage_stats,
            'encryption_enabled': ipfs_config.get('ENCRYPTION_ENABLED', True),
            'checked_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error performing IPFS health check: {str(e)}")
        return {
            'overall_health': 'error',
            'error': str(e),
            'checked_at': timezone.now().isoformat()
        }

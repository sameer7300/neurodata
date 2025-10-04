"""
Utility functions for NeuroData project.
"""
import hashlib
import uuid
import os
from decimal import Decimal
from typing import Optional, Dict, Any
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime, timedelta


def generate_unique_filename(filename: str) -> str:
    """
    Generate a unique filename to prevent collisions.
    """
    name, ext = os.path.splitext(filename)
    unique_id = uuid.uuid4().hex[:8]
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    return f"{name}_{timestamp}_{unique_id}{ext}"


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content.
    """
    return hashlib.sha256(file_content).hexdigest()


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    Validate if file extension is allowed.
    """
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def generate_api_key() -> str:
    """
    Generate a random API key.
    """
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    """
    import secrets
    return secrets.token_urlsafe(length)


def is_valid_ethereum_address(address: str) -> bool:
    """
    Validate Ethereum address format.
    """
    if not address.startswith('0x'):
        return False
    
    if len(address) != 42:
        return False
    
    try:
        int(address[2:], 16)
        return True
    except ValueError:
        return False


def wei_to_ether(wei_amount: int) -> Decimal:
    """
    Convert Wei to Ether.
    """
    return Decimal(wei_amount) / Decimal(10**18)


def ether_to_wei(ether_amount: Decimal) -> int:
    """
    Convert Ether to Wei.
    """
    return int(ether_amount * Decimal(10**18))


def create_response_data(
    success: bool = True,
    message: str = "",
    data: Any = None,
    errors: Dict = None
) -> Dict[str, Any]:
    """
    Create standardized API response data.
    """
    response = {
        'success': success,
        'timestamp': timezone.now().isoformat(),
    }
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    if errors:
        response['errors'] = errors
    
    return response


def paginate_queryset(queryset, page, page_size=20):
    """
    Simple pagination helper.
    """
    start = (page - 1) * page_size
    end = start + page_size
    return queryset[start:end]


def get_client_ip(request) -> str:
    """
    Get client IP address from request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing dangerous characters.
    """
    # Remove or replace dangerous characters
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Limit filename length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext


def calculate_dataset_score(dataset) -> float:
    """
    Calculate a quality score for a dataset based on various factors.
    """
    score = 0.0
    
    # Base score
    score += 50.0
    
    # Size factor (larger datasets get higher scores, up to a point)
    if dataset.file_size:
        size_mb = dataset.file_size / (1024 * 1024)
        if size_mb > 1:
            score += min(20.0, size_mb / 10)
    
    # Purchase count factor
    purchase_count = getattr(dataset, 'purchase_count', 0)
    score += min(15.0, purchase_count * 2)
    
    # Rating factor
    if hasattr(dataset, 'average_rating') and dataset.average_rating:
        score += (dataset.average_rating - 3) * 5  # Scale 1-5 rating to -10 to +10
    
    # Recency factor (newer datasets get slight boost)
    if dataset.created_at:
        days_old = (timezone.now() - dataset.created_at).days
        if days_old < 30:
            score += 5.0
        elif days_old < 90:
            score += 2.0
    
    # Ensure score is between 0 and 100
    return max(0.0, min(100.0, score))


def generate_dataset_preview(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Generate a preview of dataset content.
    """
    preview = {
        'columns': [],
        'sample_data': [],
        'statistics': {},
        'data_types': {}
    }
    
    try:
        if file_type == 'csv':
            import pandas as pd
            df = pd.read_csv(file_path, nrows=100)  # Read first 100 rows
            
            preview['columns'] = df.columns.tolist()
            preview['sample_data'] = df.head(5).to_dict('records')
            preview['statistics'] = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'missing_values': df.isnull().sum().to_dict()
            }
            preview['data_types'] = df.dtypes.astype(str).to_dict()
            
        elif file_type == 'json':
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                preview['sample_data'] = data[:5]
                if isinstance(data[0], dict):
                    preview['columns'] = list(data[0].keys())
                preview['statistics'] = {'record_count': len(data)}
    
    except Exception as e:
        preview['error'] = str(e)
    
    return preview


def validate_dataset_format(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Validate dataset format and return validation results.
    """
    validation = {
        'is_valid': False,
        'errors': [],
        'warnings': [],
        'metadata': {}
    }
    
    try:
        if file_type == 'csv':
            import pandas as pd
            df = pd.read_csv(file_path)
            
            # Basic validations
            if df.empty:
                validation['errors'].append('Dataset is empty')
            elif len(df.columns) == 0:
                validation['errors'].append('No columns found')
            else:
                validation['is_valid'] = True
                validation['metadata'] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'size_mb': os.path.getsize(file_path) / (1024 * 1024)
                }
                
                # Check for potential issues
                if df.isnull().sum().sum() > len(df) * 0.5:
                    validation['warnings'].append('Dataset has many missing values')
                
        elif file_type == 'json':
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not data:
                validation['errors'].append('JSON file is empty')
            else:
                validation['is_valid'] = True
                validation['metadata'] = {
                    'records': len(data) if isinstance(data, list) else 1,
                    'size_mb': os.path.getsize(file_path) / (1024 * 1024)
                }
    
    except Exception as e:
        validation['errors'].append(f'Failed to parse file: {str(e)}')
    
    return validation

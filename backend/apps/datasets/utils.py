"""
Utility functions for datasets app.
"""
import os
import hashlib
import pandas as pd
import json
from typing import Dict, Any, List, Optional
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content.
    """
    return hashlib.sha256(file_content).hexdigest()


def validate_dataset_file(file: UploadedFile) -> Dict[str, Any]:
    """
    Validate uploaded dataset file.
    
    Returns:
        Dict with validation results
    """
    validation = {
        'is_valid': False,
        'errors': [],
        'warnings': [],
        'metadata': {}
    }
    
    try:
        # Check file size
        max_size = 500 * 1024 * 1024  # 500MB
        if file.size > max_size:
            validation['errors'].append(f'File size exceeds maximum limit of 500MB')
            return validation
        
        # Check file extension
        allowed_extensions = ['.csv', '.json', '.parquet', '.xlsx', '.tsv']
        file_ext = os.path.splitext(file.name)[1].lower()
        
        if file_ext not in allowed_extensions:
            validation['errors'].append(f'Unsupported file type. Allowed: {", ".join(allowed_extensions)}')
            return validation
        
        # Basic file content validation
        try:
            file.seek(0)
            content = file.read(1024)  # Read first 1KB
            file.seek(0)
            
            if not content:
                validation['errors'].append('File appears to be empty')
                return validation
            
            # Try to decode as text for CSV/JSON/TSV
            if file_ext in ['.csv', '.json', '.tsv']:
                try:
                    content.decode('utf-8')
                except UnicodeDecodeError:
                    validation['warnings'].append('File may contain non-UTF-8 characters')
            
        except Exception as e:
            validation['errors'].append(f'Error reading file: {str(e)}')
            return validation
        
        validation['is_valid'] = True
        validation['metadata'] = {
            'file_size': file.size,
            'file_type': file_ext.replace('.', ''),
            'file_name': file.name
        }
        
    except Exception as e:
        validation['errors'].append(f'Validation error: {str(e)}')
        logger.error(f"Dataset validation error: {str(e)}")
    
    return validation


def generate_dataset_preview(file_path: str, file_type: str, max_rows: int = 100) -> Dict[str, Any]:
    """
    Generate preview data for a dataset.
    
    Args:
        file_path: Path to the dataset file
        file_type: Type of file (csv, json, etc.)
        max_rows: Maximum number of rows to process for preview
    
    Returns:
        Dict containing preview data, schema info, and statistics
    """
    preview = {
        'sample_data': [],
        'schema_info': {},
        'statistics': {},
        'columns': [],
        'data_types': {}
    }
    
    try:
        if file_type == 'csv':
            # Read CSV file
            df = pd.read_csv(file_path, nrows=max_rows)
            
            preview['columns'] = df.columns.tolist()
            preview['sample_data'] = df.head(5).to_dict('records')
            preview['data_types'] = df.dtypes.astype(str).to_dict()
            
            # Generate statistics
            preview['statistics'] = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'missing_values': df.isnull().sum().to_dict(),
                'memory_usage': df.memory_usage(deep=True).sum(),
                'numeric_columns': df.select_dtypes(include=['number']).columns.tolist(),
                'categorical_columns': df.select_dtypes(include=['object']).columns.tolist()
            }
            
            # Schema information
            preview['schema_info'] = {
                'columns': [
                    {
                        'name': col,
                        'type': str(df[col].dtype),
                        'null_count': int(df[col].isnull().sum()),
                        'unique_count': int(df[col].nunique()),
                        'sample_values': df[col].dropna().head(3).tolist()
                    }
                    for col in df.columns
                ]
            }
            
        elif file_type == 'json':
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                preview['sample_data'] = data[:5]
                
                if isinstance(data[0], dict):
                    preview['columns'] = list(data[0].keys())
                    
                    # Generate basic statistics
                    preview['statistics'] = {
                        'total_records': len(data),
                        'record_type': 'object',
                        'sample_keys': list(data[0].keys()) if data else []
                    }
                    
                    # Schema information
                    if data:
                        sample_record = data[0]
                        preview['schema_info'] = {
                            'fields': [
                                {
                                    'name': key,
                                    'type': type(value).__name__,
                                    'sample_value': value
                                }
                                for key, value in sample_record.items()
                            ]
                        }
            
            elif isinstance(data, dict):
                preview['sample_data'] = [data]
                preview['statistics'] = {
                    'record_type': 'single_object',
                    'keys': list(data.keys())
                }
        
        elif file_type == 'parquet':
            # Read Parquet file
            df = pd.read_parquet(file_path)
            
            # Limit rows for preview
            df_preview = df.head(max_rows)
            
            preview['columns'] = df.columns.tolist()
            preview['sample_data'] = df_preview.head(5).to_dict('records')
            preview['data_types'] = df.dtypes.astype(str).to_dict()
            
            preview['statistics'] = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'file_size': os.path.getsize(file_path),
                'memory_usage': df.memory_usage(deep=True).sum()
            }
        
        elif file_type == 'xlsx':
            # Read Excel file
            df = pd.read_excel(file_path, nrows=max_rows)
            
            preview['columns'] = df.columns.tolist()
            preview['sample_data'] = df.head(5).to_dict('records')
            preview['data_types'] = df.dtypes.astype(str).to_dict()
            
            preview['statistics'] = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'missing_values': df.isnull().sum().to_dict()
            }
        
        # Add file-level metadata
        if os.path.exists(file_path):
            file_stats = os.stat(file_path)
            preview['file_metadata'] = {
                'size_bytes': file_stats.st_size,
                'created_time': file_stats.st_ctime,
                'modified_time': file_stats.st_mtime
            }
    
    except Exception as e:
        logger.error(f"Error generating dataset preview: {str(e)}")
        preview['error'] = str(e)
    
    return preview


def upload_to_ipfs(file_path: str) -> Dict[str, str]:
    """
    Upload file to IPFS and return hash and URL.
    
    Args:
        file_path: Local path to the file
    
    Returns:
        Dict with IPFS hash and URL
    """
    result = {
        'ipfs_hash': '',
        'ipfs_url': '',
        'error': None
    }
    
    try:
        # Import IPFS client
        import ipfshttpclient
        
        # Connect to IPFS node
        ipfs_api_url = getattr(settings, 'IPFS_API_URL', 'http://localhost:5001')
        client = ipfshttpclient.connect(ipfs_api_url)
        
        # Upload file
        response = client.add(file_path)
        
        if isinstance(response, list):
            ipfs_hash = response[0]['Hash']
        else:
            ipfs_hash = response['Hash']
        
        # Generate IPFS URL
        ipfs_gateway = getattr(settings, 'IPFS_GATEWAY_URL', 'http://localhost:8080')
        ipfs_url = f"{ipfs_gateway}/ipfs/{ipfs_hash}"
        
        result['ipfs_hash'] = ipfs_hash
        result['ipfs_url'] = ipfs_url
        
        logger.info(f"File uploaded to IPFS: {ipfs_hash}")
        
    except Exception as e:
        error_msg = f"IPFS upload failed: {str(e)}"
        logger.error(error_msg)
        result['error'] = error_msg
    
    return result


def calculate_dataset_quality_score(dataset) -> float:
    """
    Calculate quality score for a dataset based on various factors.
    
    Args:
        dataset: Dataset instance
    
    Returns:
        Quality score between 0 and 100
    """
    score = 0.0
    
    try:
        # Base score
        score += 20.0
        
        # Description quality (0-15 points)
        if dataset.description:
            desc_length = len(dataset.description)
            if desc_length > 100:
                score += 15.0
            elif desc_length > 50:
                score += 10.0
            elif desc_length > 20:
                score += 5.0
        
        # File size factor (0-10 points)
        if dataset.file_size:
            size_mb = dataset.file_size / (1024 * 1024)
            if size_mb > 10:  # Larger datasets get higher scores
                score += min(10.0, size_mb / 100)
        
        # Schema information (0-15 points)
        if dataset.schema_info:
            if 'columns' in dataset.schema_info:
                column_count = len(dataset.schema_info.get('columns', []))
                score += min(15.0, column_count * 1.5)
        
        # Sample data availability (0-10 points)
        if dataset.sample_data:
            score += 10.0
        
        # Category and tags (0-10 points)
        if dataset.category:
            score += 5.0
        if dataset.tags.exists():
            score += min(5.0, dataset.tags.count())
        
        # User engagement (0-20 points)
        if dataset.download_count > 0:
            score += min(10.0, dataset.download_count / 10)
        
        if dataset.rating_count > 0:
            rating_bonus = (dataset.rating_average - 3) * 5  # Scale 1-5 rating to -10 to +10
            score += max(0, min(10.0, rating_bonus))
        
        # License information (0-5 points)
        if dataset.license_type and dataset.license_type != 'custom':
            score += 5.0
        elif dataset.license_text:
            score += 3.0
        
        # Keywords (0-5 points)
        if dataset.keywords:
            keyword_count = len(dataset.keywords.split(','))
            score += min(5.0, keyword_count)
    
    except Exception as e:
        logger.error(f"Error calculating quality score: {str(e)}")
    
    # Ensure score is between 0 and 100
    return max(0.0, min(100.0, score))


def generate_dataset_recommendations(user, limit: int = 10) -> List[Dict]:
    """
    Generate dataset recommendations for a user.
    
    Args:
        user: User instance
        limit: Maximum number of recommendations
    
    Returns:
        List of recommended datasets
    """
    from .models import Dataset
    from apps.marketplace.models import Purchase
    
    recommendations = []
    
    try:
        # Get user's purchase history
        purchased_datasets = Purchase.objects.filter(
            buyer=user,
            status='completed'
        ).values_list('dataset_id', flat=True)
        
        # Get categories from purchased datasets
        if purchased_datasets:
            purchased_categories = Dataset.objects.filter(
                id__in=purchased_datasets
            ).values_list('category_id', flat=True).distinct()
            
            # Recommend datasets from same categories
            category_recommendations = Dataset.objects.filter(
                category_id__in=purchased_categories,
                status='approved'
            ).exclude(
                id__in=purchased_datasets
            ).exclude(
                owner=user
            ).order_by('-rating_average', '-download_count')[:limit//2]
            
            recommendations.extend(category_recommendations)
        
        # Fill remaining slots with popular datasets
        remaining_slots = limit - len(recommendations)
        if remaining_slots > 0:
            popular_datasets = Dataset.objects.filter(
                status='approved'
            ).exclude(
                id__in=purchased_datasets
            ).exclude(
                owner=user
            ).exclude(
                id__in=[d.id for d in recommendations]
            ).order_by('-download_count', '-rating_average')[:remaining_slots]
            
            recommendations.extend(popular_datasets)
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
    
    return recommendations


def search_datasets(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search datasets based on query parameters.
    
    Args:
        query_params: Dictionary of search parameters
    
    Returns:
        Dict with search results and metadata
    """
    from .models import Dataset
    from django.db.models import Q
    
    # Start with approved datasets
    queryset = Dataset.objects.filter(status='approved')
    
    # Text search
    if query_params.get('q'):
        search_query = query_params['q']
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(keywords__icontains=search_query)
        )
    
    # Category filter
    if query_params.get('category'):
        queryset = queryset.filter(category=query_params['category'])
    
    # Tags filter
    if query_params.get('tags'):
        queryset = queryset.filter(tags__in=query_params['tags']).distinct()
    
    # Price filters
    if query_params.get('price_min') is not None:
        queryset = queryset.filter(price__gte=query_params['price_min'])
    
    if query_params.get('price_max') is not None:
        queryset = queryset.filter(price__lte=query_params['price_max'])
    
    # Free datasets filter
    if query_params.get('is_free'):
        queryset = queryset.filter(price=0)
    
    # File type filter
    if query_params.get('file_type'):
        queryset = queryset.filter(file_type=query_params['file_type'])
    
    # Sorting
    sort_by = query_params.get('sort_by', '-created_at')
    queryset = queryset.order_by(sort_by)
    
    return {
        'queryset': queryset,
        'total_count': queryset.count()
    }


def get_dataset_analytics(dataset) -> Dict[str, Any]:
    """
    Get analytics data for a dataset.
    
    Args:
        dataset: Dataset instance
    
    Returns:
        Dict with analytics data
    """
    from apps.marketplace.models import Purchase
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta
    
    analytics = {}
    
    try:
        # Basic metrics
        analytics['total_views'] = dataset.view_count
        analytics['total_downloads'] = dataset.download_count
        analytics['total_purchases'] = Purchase.objects.filter(
            dataset=dataset,
            status='completed'
        ).count()
        
        # Revenue
        revenue = Purchase.objects.filter(
            dataset=dataset,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        analytics['total_revenue'] = str(revenue)
        
        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        recent_purchases = Purchase.objects.filter(
            dataset=dataset,
            status='completed',
            created_at__gte=thirty_days_ago
        ).count()
        
        recent_views = dataset.access_logs.filter(
            access_type='view',
            timestamp__gte=thirty_days_ago
        ).count()
        
        analytics['recent_activity'] = {
            'purchases_30d': recent_purchases,
            'views_30d': recent_views
        }
        
        # Rating breakdown
        reviews = dataset.reviews.filter(is_approved=True)
        rating_breakdown = {}
        for i in range(1, 6):
            rating_breakdown[f'{i}_star'] = reviews.filter(rating=i).count()
        
        analytics['rating_breakdown'] = rating_breakdown
        
        # Top countries (if available)
        # This would require IP geolocation data
        analytics['top_countries'] = []
        
    except Exception as e:
        logger.error(f"Error getting dataset analytics: {str(e)}")
    
    return analytics

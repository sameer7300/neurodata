"""
Validators for datasets app.
"""
import os
import pandas as pd
import json
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def validate_dataset_file_size(file: UploadedFile) -> None:
    """
    Validate dataset file size.
    
    Args:
        file: Uploaded file object
    
    Raises:
        ValidationError: If file size exceeds limit
    """
    max_size = getattr(settings, 'MAX_DATASET_SIZE', 500 * 1024 * 1024)  # 500MB default
    
    if file.size > max_size:
        raise ValidationError(
            f'File size ({file.size} bytes) exceeds maximum allowed size '
            f'({max_size} bytes).'
        )


def validate_dataset_file_type(file: UploadedFile) -> None:
    """
    Validate dataset file type.
    
    Args:
        file: Uploaded file object
    
    Raises:
        ValidationError: If file type is not supported
    """
    allowed_extensions = getattr(settings, 'ALLOWED_DATASET_EXTENSIONS', [
        '.csv', '.json', '.parquet', '.xlsx', '.tsv', '.jsonl'
    ])
    
    file_ext = os.path.splitext(file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise ValidationError(
            f'File type "{file_ext}" is not supported. '
            f'Allowed types: {", ".join(allowed_extensions)}'
        )


def validate_csv_file(file: UploadedFile) -> Dict[str, Any]:
    """
    Validate CSV file structure and content.
    
    Args:
        file: Uploaded CSV file
    
    Returns:
        Dict with validation results
    
    Raises:
        ValidationError: If CSV file is invalid
    """
    validation_result = {
        'is_valid': True,
        'warnings': [],
        'metadata': {}
    }
    
    try:
        # Reset file pointer
        file.seek(0)
        
        # Try to read the CSV file
        df = pd.read_csv(file, nrows=1000)  # Read first 1000 rows for validation
        
        # Check if file is empty
        if df.empty:
            raise ValidationError('CSV file is empty or contains no data.')
        
        # Check for minimum columns
        if len(df.columns) < 1:
            raise ValidationError('CSV file must contain at least one column.')
        
        # Check for duplicate column names
        if len(df.columns) != len(set(df.columns)):
            validation_result['warnings'].append('CSV file contains duplicate column names.')
        
        # Check for completely empty columns
        empty_columns = df.columns[df.isnull().all()].tolist()
        if empty_columns:
            validation_result['warnings'].append(
                f'The following columns are completely empty: {", ".join(empty_columns)}'
            )
        
        # Store metadata
        validation_result['metadata'] = {
            'columns': df.columns.tolist(),
            'row_count': len(df),
            'column_count': len(df.columns),
            'data_types': df.dtypes.astype(str).to_dict(),
            'missing_values': df.isnull().sum().to_dict()
        }
        
    except pd.errors.EmptyDataError:
        raise ValidationError('CSV file is empty or contains no data.')
    except pd.errors.ParserError as e:
        raise ValidationError(f'CSV file parsing error: {str(e)}')
    except Exception as e:
        logger.error(f'CSV validation error: {str(e)}')
        raise ValidationError(f'Error validating CSV file: {str(e)}')
    finally:
        file.seek(0)  # Reset file pointer
    
    return validation_result


def validate_json_file(file: UploadedFile) -> Dict[str, Any]:
    """
    Validate JSON file structure and content.
    
    Args:
        file: Uploaded JSON file
    
    Returns:
        Dict with validation results
    
    Raises:
        ValidationError: If JSON file is invalid
    """
    validation_result = {
        'is_valid': True,
        'warnings': [],
        'metadata': {}
    }
    
    try:
        # Reset file pointer
        file.seek(0)
        
        # Try to parse JSON
        content = file.read().decode('utf-8')
        data = json.loads(content)
        
        # Check if data is empty
        if not data:
            raise ValidationError('JSON file is empty or contains no data.')
        
        # Analyze structure
        if isinstance(data, list):
            validation_result['metadata'] = {
                'type': 'array',
                'record_count': len(data),
                'sample_record': data[0] if data else None
            }
            
            # Check for consistent structure in array
            if data and isinstance(data[0], dict):
                first_keys = set(data[0].keys())
                inconsistent_records = []
                
                for i, record in enumerate(data[:100]):  # Check first 100 records
                    if isinstance(record, dict) and set(record.keys()) != first_keys:
                        inconsistent_records.append(i)
                
                if inconsistent_records:
                    validation_result['warnings'].append(
                        f'Records at positions {inconsistent_records[:5]} have '
                        f'different keys than the first record.'
                    )
        
        elif isinstance(data, dict):
            validation_result['metadata'] = {
                'type': 'object',
                'keys': list(data.keys()),
                'key_count': len(data.keys())
            }
        
        else:
            validation_result['metadata'] = {
                'type': type(data).__name__,
                'value': str(data)[:100]  # First 100 characters
            }
    
    except json.JSONDecodeError as e:
        raise ValidationError(f'Invalid JSON format: {str(e)}')
    except UnicodeDecodeError:
        raise ValidationError('JSON file contains invalid UTF-8 characters.')
    except Exception as e:
        logger.error(f'JSON validation error: {str(e)}')
        raise ValidationError(f'Error validating JSON file: {str(e)}')
    finally:
        file.seek(0)  # Reset file pointer
    
    return validation_result


def validate_excel_file(file: UploadedFile) -> Dict[str, Any]:
    """
    Validate Excel file structure and content.
    
    Args:
        file: Uploaded Excel file
    
    Returns:
        Dict with validation results
    
    Raises:
        ValidationError: If Excel file is invalid
    """
    validation_result = {
        'is_valid': True,
        'warnings': [],
        'metadata': {}
    }
    
    try:
        # Reset file pointer
        file.seek(0)
        
        # Try to read Excel file
        df = pd.read_excel(file, nrows=1000)  # Read first 1000 rows
        
        # Check if file is empty
        if df.empty:
            raise ValidationError('Excel file is empty or contains no data.')
        
        # Check for minimum columns
        if len(df.columns) < 1:
            raise ValidationError('Excel file must contain at least one column.')
        
        # Store metadata
        validation_result['metadata'] = {
            'columns': df.columns.tolist(),
            'row_count': len(df),
            'column_count': len(df.columns),
            'data_types': df.dtypes.astype(str).to_dict()
        }
        
        # Check for merged cells or complex formatting
        if df.columns.str.contains('Unnamed:').any():
            validation_result['warnings'].append(
                'Excel file may contain merged cells or complex formatting.'
            )
    
    except Exception as e:
        logger.error(f'Excel validation error: {str(e)}')
        raise ValidationError(f'Error validating Excel file: {str(e)}')
    finally:
        file.seek(0)  # Reset file pointer
    
    return validation_result


def validate_parquet_file(file: UploadedFile) -> Dict[str, Any]:
    """
    Validate Parquet file structure and content.
    
    Args:
        file: Uploaded Parquet file
    
    Returns:
        Dict with validation results
    
    Raises:
        ValidationError: If Parquet file is invalid
    """
    validation_result = {
        'is_valid': True,
        'warnings': [],
        'metadata': {}
    }
    
    try:
        # Reset file pointer
        file.seek(0)
        
        # Save file temporarily to read with pandas
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as tmp_file:
            tmp_file.write(file.read())
            tmp_file.flush()
            
            # Read parquet file
            df = pd.read_parquet(tmp_file.name)
            
            # Clean up temp file
            os.unlink(tmp_file.name)
        
        # Check if file is empty
        if df.empty:
            raise ValidationError('Parquet file is empty or contains no data.')
        
        # Store metadata
        validation_result['metadata'] = {
            'columns': df.columns.tolist(),
            'row_count': len(df),
            'column_count': len(df.columns),
            'data_types': df.dtypes.astype(str).to_dict()
        }
    
    except Exception as e:
        logger.error(f'Parquet validation error: {str(e)}')
        raise ValidationError(f'Error validating Parquet file: {str(e)}')
    finally:
        file.seek(0)  # Reset file pointer
    
    return validation_result


def validate_dataset_file_content(file: UploadedFile) -> Dict[str, Any]:
    """
    Validate dataset file content based on file type.
    
    Args:
        file: Uploaded file object
    
    Returns:
        Dict with validation results
    
    Raises:
        ValidationError: If file content is invalid
    """
    file_ext = os.path.splitext(file.name)[1].lower()
    
    # Validate based on file type
    if file_ext == '.csv':
        return validate_csv_file(file)
    elif file_ext == '.json':
        return validate_json_file(file)
    elif file_ext in ['.xlsx', '.xls']:
        return validate_excel_file(file)
    elif file_ext == '.parquet':
        return validate_parquet_file(file)
    elif file_ext == '.tsv':
        # TSV is similar to CSV but with tab separator
        # We can reuse CSV validation logic
        return validate_csv_file(file)
    else:
        # For other file types, just do basic validation
        return {
            'is_valid': True,
            'warnings': [],
            'metadata': {
                'file_size': file.size,
                'file_name': file.name
            }
        }


def validate_dataset_metadata(title: str, description: str, price: float) -> None:
    """
    Validate dataset metadata.
    
    Args:
        title: Dataset title
        description: Dataset description
        price: Dataset price
    
    Raises:
        ValidationError: If metadata is invalid
    """
    # Validate title
    if not title or len(title.strip()) < 3:
        raise ValidationError('Dataset title must be at least 3 characters long.')
    
    if len(title) > 200:
        raise ValidationError('Dataset title cannot exceed 200 characters.')
    
    # Validate description
    if not description or len(description.strip()) < 10:
        raise ValidationError('Dataset description must be at least 10 characters long.')
    
    if len(description) > 5000:
        raise ValidationError('Dataset description cannot exceed 5000 characters.')
    
    # Validate price
    if price < 0:
        raise ValidationError('Dataset price cannot be negative.')
    
    max_price = 10000.0  # Maximum price in NRC
    if price > max_price:
        raise ValidationError(f'Dataset price cannot exceed {max_price} NRC.')


def validate_dataset_keywords(keywords: str) -> None:
    """
    Validate dataset keywords.
    
    Args:
        keywords: Comma-separated keywords
    
    Raises:
        ValidationError: If keywords are invalid
    """
    if not keywords:
        return
    
    keyword_list = [kw.strip() for kw in keywords.split(',')]
    
    # Check maximum number of keywords
    if len(keyword_list) > 20:
        raise ValidationError('Maximum 20 keywords are allowed.')
    
    # Check individual keyword length
    for keyword in keyword_list:
        if len(keyword) > 50:
            raise ValidationError('Each keyword cannot exceed 50 characters.')
        
        if len(keyword) < 2:
            raise ValidationError('Each keyword must be at least 2 characters long.')


def validate_complete_dataset(file: UploadedFile, title: str, description: str, 
                            price: float, keywords: str = '') -> Dict[str, Any]:
    """
    Perform complete validation of a dataset.
    
    Args:
        file: Uploaded file object
        title: Dataset title
        description: Dataset description
        price: Dataset price
        keywords: Dataset keywords
    
    Returns:
        Dict with complete validation results
    
    Raises:
        ValidationError: If any validation fails
    """
    validation_result = {
        'is_valid': True,
        'warnings': [],
        'metadata': {},
        'file_validation': {}
    }
    
    try:
        # Validate file size and type
        validate_dataset_file_size(file)
        validate_dataset_file_type(file)
        
        # Validate file content
        file_validation = validate_dataset_file_content(file)
        validation_result['file_validation'] = file_validation
        validation_result['warnings'].extend(file_validation.get('warnings', []))
        validation_result['metadata'].update(file_validation.get('metadata', {}))
        
        # Validate metadata
        validate_dataset_metadata(title, description, price)
        
        # Validate keywords
        if keywords:
            validate_dataset_keywords(keywords)
        
        logger.info(f'Dataset validation completed successfully for: {title}')
        
    except ValidationError:
        validation_result['is_valid'] = False
        raise
    except Exception as e:
        logger.error(f'Unexpected error during dataset validation: {str(e)}')
        validation_result['is_valid'] = False
        raise ValidationError(f'Validation error: {str(e)}')
    
    return validation_result

"""
Django management command for IPFS operations and maintenance.
"""
import logging
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from core.ipfs_service import ipfs_service
from core.ipfs_utils import IPFSUtils, get_ipfs_health_check, validate_dataset_file
from core.ipfs_providers import test_provider_connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage IPFS operations and maintenance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['status', 'test', 'stats', 'cleanup', 'validate', 'health'],
            help='Action to perform'
        )
        parser.add_argument(
            '--provider',
            type=str,
            help='IPFS provider to test (pinata, web3_storage, infura, local)'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='File path for validation'
        )
        parser.add_argument(
            '--cleanup-hours',
            type=int,
            default=24,
            help='Maximum age in hours for temp file cleanup'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        action = options['action']
        
        if action == 'status':
            self._show_status()
        elif action == 'test':
            self._test_connection(options.get('provider'))
        elif action == 'stats':
            self._show_stats()
        elif action == 'cleanup':
            self._cleanup_temp_files(options['cleanup_hours'])
        elif action == 'validate':
            self._validate_file(options.get('file'))
        elif action == 'health':
            self._health_check()
    
    def _show_status(self):
        """Show IPFS service status."""
        self.stdout.write(self.style.SUCCESS('📊 IPFS Service Status'))
        self.stdout.write('=' * 50)
        
        try:
            # Get configuration
            ipfs_config = getattr(settings, 'IPFS_CONFIG', {})
            provider = ipfs_config.get('PROVIDER', 'pinata')
            encryption_enabled = ipfs_config.get('ENCRYPTION_ENABLED', True)
            
            self.stdout.write(f'Provider: {provider}')
            self.stdout.write(f'Encryption: {"Enabled" if encryption_enabled else "Disabled"}')
            self.stdout.write(f'Gateway URL: {ipfs_service.gateway_url}')
            self.stdout.write(f'Cache Timeout: {ipfs_service.cache_timeout} seconds')
            
            # Test connection
            self.stdout.write('\n🔗 Connection Test:')
            connection_test = test_provider_connection(provider, ipfs_config)
            
            if connection_test['success']:
                self.stdout.write(self.style.SUCCESS('✅ Connection successful'))
                if 'test_hash' in connection_test:
                    self.stdout.write(f'Test hash: {connection_test["test_hash"]}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Connection failed: {connection_test["error"]}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error getting status: {str(e)}'))
    
    def _test_connection(self, provider=None):
        """Test IPFS provider connection."""
        self.stdout.write(self.style.SUCCESS('🧪 Testing IPFS Connection'))
        self.stdout.write('=' * 50)
        
        try:
            ipfs_config = getattr(settings, 'IPFS_CONFIG', {})
            
            if provider:
                test_provider = provider
            else:
                test_provider = ipfs_config.get('PROVIDER', 'pinata')
            
            self.stdout.write(f'Testing provider: {test_provider}')
            
            # Test connection
            result = test_provider_connection(test_provider, ipfs_config)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS('✅ Connection test passed'))
                self.stdout.write(f'Message: {result.get("message", "")}')
                if 'test_hash' in result:
                    self.stdout.write(f'Test file hash: {result["test_hash"]}')
                if 'upload_size' in result:
                    self.stdout.write(f'Upload size: {result["upload_size"]} bytes')
            else:
                self.stdout.write(self.style.ERROR('❌ Connection test failed'))
                self.stdout.write(f'Error: {result.get("error", "Unknown error")}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Test error: {str(e)}'))
    
    def _show_stats(self):
        """Show storage statistics."""
        self.stdout.write(self.style.SUCCESS('📈 Storage Statistics'))
        self.stdout.write('=' * 50)
        
        try:
            stats = IPFSUtils.get_dataset_storage_stats()
            
            if 'error' in stats:
                self.stdout.write(self.style.ERROR(f'❌ Error: {stats["error"]}'))
                return
            
            self.stdout.write(f'Total datasets: {stats["total_datasets"]}')
            self.stdout.write(f'Total storage: {stats["total_size_formatted"]}')
            self.stdout.write(f'Encrypted datasets: {stats["encrypted_datasets"]} ({stats["encryption_percentage"]:.1f}%)')
            self.stdout.write(f'Recent uploads (30 days): {stats["recent_uploads_30_days"]}')
            
            if stats["total_datasets"] > 0:
                avg_size = IPFSUtils.format_file_size(stats["average_file_size"])
                self.stdout.write(f'Average file size: {avg_size}')
            
            # File types breakdown
            if stats["file_types"]:
                self.stdout.write('\n📁 File Types:')
                for file_type, type_stats in stats["file_types"].items():
                    size_formatted = IPFSUtils.format_file_size(type_stats["size"])
                    self.stdout.write(f'  {file_type}: {type_stats["count"]} files, {size_formatted}')
            
            self.stdout.write(f'\nGenerated at: {stats["generated_at"]}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error getting stats: {str(e)}'))
    
    def _cleanup_temp_files(self, max_age_hours):
        """Clean up temporary files."""
        self.stdout.write(self.style.SUCCESS(f'🧹 Cleaning up temp files older than {max_age_hours} hours'))
        self.stdout.write('=' * 50)
        
        try:
            temp_dir = getattr(settings, 'TEMP_DIR', '/tmp')
            
            if not os.path.exists(temp_dir):
                self.stdout.write(self.style.WARNING(f'⚠️  Temp directory not found: {temp_dir}'))
                return
            
            # Count files before cleanup
            files_before = len([f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))])
            
            # Perform cleanup
            IPFSUtils.cleanup_temp_files(temp_dir, max_age_hours)
            
            # Count files after cleanup
            files_after = len([f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))])
            
            cleaned_count = files_before - files_after
            
            if cleaned_count > 0:
                self.stdout.write(self.style.SUCCESS(f'✅ Cleaned up {cleaned_count} files'))
            else:
                self.stdout.write('ℹ️  No files needed cleanup')
            
            self.stdout.write(f'Files remaining: {files_after}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Cleanup error: {str(e)}'))
    
    def _validate_file(self, file_path):
        """Validate a dataset file."""
        if not file_path:
            self.stdout.write(self.style.ERROR('❌ File path is required. Use --file option.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'🔍 Validating file: {file_path}'))
        self.stdout.write('=' * 50)
        
        try:
            if not os.path.exists(file_path):
                self.stdout.write(self.style.ERROR('❌ File not found'))
                return
            
            # Validate file
            validation_result = validate_dataset_file(file_path)
            
            if validation_result['valid']:
                self.stdout.write(self.style.SUCCESS('✅ File validation passed'))
            else:
                self.stdout.write(self.style.ERROR('❌ File validation failed'))
                for error in validation_result['errors']:
                    self.stdout.write(f'  Error: {error}')
            
            # Show warnings
            if validation_result['warnings']:
                self.stdout.write(self.style.WARNING('\n⚠️  Warnings:'))
                for warning in validation_result['warnings']:
                    self.stdout.write(f'  {warning}')
            
            # Show file info
            if validation_result['file_info']:
                file_info = validation_result['file_info']
                self.stdout.write('\n📄 File Information:')
                self.stdout.write(f'  Size: {IPFSUtils.format_file_size(file_info["file_size"])}')
                self.stdout.write(f'  Type: {file_info["mime_type"] or "Unknown"}')
                self.stdout.write(f'  Extension: {file_info["file_extension"]}')
                self.stdout.write(f'  SHA256: {file_info["sha256_hash"]}')
                self.stdout.write(f'  MD5: {file_info["md5_hash"]}')
            
            # Show upload estimate
            if validation_result['upload_estimate']:
                estimate = validation_result['upload_estimate']
                if 'error' not in estimate:
                    self.stdout.write('\n⏱️  Upload Estimate:')
                    self.stdout.write(f'  Estimated time: {estimate["estimated_time_formatted"]}')
                    self.stdout.write(f'  File size: {estimate["file_size_mb"]:.2f} MB')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Validation error: {str(e)}'))
    
    def _health_check(self):
        """Perform comprehensive health check."""
        self.stdout.write(self.style.SUCCESS('🏥 IPFS Health Check'))
        self.stdout.write('=' * 50)
        
        try:
            health_result = get_ipfs_health_check()
            
            # Overall health
            if health_result['overall_health'] == 'healthy':
                self.stdout.write(self.style.SUCCESS('✅ Overall health: HEALTHY'))
            elif health_result['overall_health'] == 'unhealthy':
                self.stdout.write(self.style.ERROR('❌ Overall health: UNHEALTHY'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Overall health: ERROR - {health_result.get("error", "Unknown")}'))
                return
            
            # Provider info
            self.stdout.write(f'\n🔗 Provider: {health_result["provider"]}')
            self.stdout.write(f'Encryption: {"Enabled" if health_result["encryption_enabled"] else "Disabled"}')
            
            # Connection test
            connection_test = health_result['connection_test']
            if connection_test['success']:
                self.stdout.write(self.style.SUCCESS('✅ Connection: OK'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Connection: FAILED - {connection_test.get("error", "Unknown")}'))
            
            # Cache test
            if health_result['cache_working']:
                self.stdout.write(self.style.SUCCESS('✅ Cache: OK'))
            else:
                self.stdout.write(self.style.ERROR('❌ Cache: FAILED'))
            
            # Storage stats
            storage_stats = health_result['storage_stats']
            if 'error' not in storage_stats:
                self.stdout.write(f'\n📊 Storage Stats:')
                self.stdout.write(f'  Total datasets: {storage_stats["total_datasets"]}')
                self.stdout.write(f'  Total size: {storage_stats["total_size_formatted"]}')
                self.stdout.write(f'  Encrypted: {storage_stats["encrypted_datasets"]} ({storage_stats["encryption_percentage"]:.1f}%)')
            
            self.stdout.write(f'\nChecked at: {health_result["checked_at"]}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Health check error: {str(e)}'))

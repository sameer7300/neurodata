"""
Management command to clean up duplicate datasets for testing.
"""
from django.core.management.base import BaseCommand
from apps.datasets.models import Dataset


class Command(BaseCommand):
    help = 'Clean up duplicate datasets (for testing purposes)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually delete the duplicates (without this, just shows what would be deleted)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Checking for duplicate datasets...')
        
        # Find datasets with duplicate file hashes
        duplicates = []
        seen_hashes = set()
        
        for dataset in Dataset.objects.all().order_by('created_at'):
            if dataset.file_hash in seen_hashes:
                duplicates.append(dataset)
            else:
                seen_hashes.add(dataset.file_hash)
        
        if not duplicates:
            self.stdout.write(self.style.SUCCESS('No duplicate datasets found.'))
            return
        
        self.stdout.write(f'Found {len(duplicates)} duplicate datasets:')
        
        for dataset in duplicates:
            self.stdout.write(f'  - {dataset.title} (ID: {dataset.id}) - {dataset.file_name}')
        
        if options['confirm']:
            for dataset in duplicates:
                self.stdout.write(f'Deleting: {dataset.title}')
                dataset.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {len(duplicates)} duplicate datasets.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Run with --confirm to actually delete these {len(duplicates)} duplicates.'
                )
            )

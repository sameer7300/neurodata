"""
Management command to approve datasets for testing.
"""
from django.core.management.base import BaseCommand
from apps.datasets.models import Dataset


class Command(BaseCommand):
    help = 'Approve all draft datasets (for testing purposes)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Approve all draft datasets',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Approve datasets for specific user (username)',
        )

    def handle(self, *args, **options):
        queryset = Dataset.objects.filter(status='draft')
        
        if options['user']:
            queryset = queryset.filter(owner__username=options['user'])
            self.stdout.write(f'Filtering datasets for user: {options["user"]}')
        
        draft_datasets = list(queryset)
        
        if not draft_datasets:
            self.stdout.write(self.style.SUCCESS('No draft datasets found to approve.'))
            return
        
        self.stdout.write(f'Found {len(draft_datasets)} draft datasets:')
        
        for dataset in draft_datasets:
            self.stdout.write(f'  - {dataset.title} by {dataset.owner.username} (Status: {dataset.status})')
        
        if options['all'] or options['user']:
            for dataset in draft_datasets:
                dataset.status = 'approved'
                dataset.save()
                self.stdout.write(f'Approved: {dataset.title}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Approved {len(draft_datasets)} datasets.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Run with --all to approve all {len(draft_datasets)} draft datasets, '
                    f'or --user <username> to approve datasets for a specific user.'
                )
            )

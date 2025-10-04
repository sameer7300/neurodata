"""
Management command to create sample categories and tags for testing.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.datasets.models import Category, Tag


class Command(BaseCommand):
    help = 'Create sample categories and tags for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample categories...')
        
        # Sample categories
        categories_data = [
            {
                'name': 'Computer Vision',
                'description': 'Datasets for image recognition, object detection, and visual analysis',
                'icon': 'fas fa-eye'
            },
            {
                'name': 'Natural Language Processing',
                'description': 'Text datasets for language understanding and generation',
                'icon': 'fas fa-language'
            },
            {
                'name': 'Time Series',
                'description': 'Sequential data for forecasting and trend analysis',
                'icon': 'fas fa-chart-line'
            },
            {
                'name': 'Healthcare',
                'description': 'Medical and health-related datasets',
                'icon': 'fas fa-heartbeat'
            },
            {
                'name': 'Finance',
                'description': 'Financial markets and economic datasets',
                'icon': 'fas fa-coins'
            },
            {
                'name': 'Audio & Speech',
                'description': 'Sound, music, and speech recognition datasets',
                'icon': 'fas fa-microphone'
            },
            {
                'name': 'Tabular Data',
                'description': 'Structured data in tables and spreadsheets',
                'icon': 'fas fa-table'
            },
            {
                'name': 'Geospatial',
                'description': 'Geographic and location-based datasets',
                'icon': 'fas fa-map-marked-alt'
            },
            {
                'name': 'Social Media',
                'description': 'Social network and user behavior datasets',
                'icon': 'fas fa-share-alt'
            },
            {
                'name': 'IoT & Sensors',
                'description': 'Internet of Things and sensor data',
                'icon': 'fas fa-wifi'
            }
        ]
        
        created_categories = 0
        for cat_data in categories_data:
            slug = slugify(cat_data['name'])
            category, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'is_active': True
                }
            )
            if created:
                created_categories += 1
                self.stdout.write(f'  ✓ Created category: {category.name}')
            else:
                self.stdout.write(f'  - Category already exists: {category.name}')
        
        self.stdout.write('Creating sample tags...')
        
        # Sample tags
        tags_data = [
            {'name': 'classification', 'color': '#007bff'},
            {'name': 'regression', 'color': '#28a745'},
            {'name': 'clustering', 'color': '#ffc107'},
            {'name': 'deep-learning', 'color': '#dc3545'},
            {'name': 'supervised', 'color': '#6f42c1'},
            {'name': 'unsupervised', 'color': '#fd7e14'},
            {'name': 'reinforcement', 'color': '#20c997'},
            {'name': 'neural-networks', 'color': '#e83e8c'},
            {'name': 'machine-learning', 'color': '#6c757d'},
            {'name': 'data-science', 'color': '#17a2b8'},
            {'name': 'preprocessing', 'color': '#343a40'},
            {'name': 'feature-engineering', 'color': '#495057'},
            {'name': 'benchmark', 'color': '#f8f9fa'},
            {'name': 'research', 'color': '#dee2e6'},
            {'name': 'production', 'color': '#ced4da'}
        ]
        
        created_tags = 0
        for tag_data in tags_data:
            slug = slugify(tag_data['name'])
            tag, created = Tag.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': tag_data['name'],
                    'color': tag_data['color']
                }
            )
            if created:
                created_tags += 1
                self.stdout.write(f'  ✓ Created tag: {tag.name}')
            else:
                self.stdout.write(f'  - Tag already exists: {tag.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSample data creation completed!\n'
                f'Created {created_categories} new categories and {created_tags} new tags.'
            )
        )

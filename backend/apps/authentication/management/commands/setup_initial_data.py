"""
Management command to setup initial data for NeuroData platform.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.datasets.models import Category, Tag
from apps.ml_training.models import MLAlgorithm, ComputeResource
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup initial data for NeuroData platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-categories',
            action='store_true',
            help='Skip creating dataset categories',
        )
        parser.add_argument(
            '--skip-algorithms',
            action='store_true',
            help='Skip creating ML algorithms',
        )
        parser.add_argument(
            '--skip-resources',
            action='store_true',
            help='Skip creating compute resources',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up initial data for NeuroData...'))

        if not options['skip_categories']:
            self.create_categories()
            self.create_tags()

        if not options['skip_algorithms']:
            self.create_ml_algorithms()

        if not options['skip_resources']:
            self.create_compute_resources()

        self.stdout.write(self.style.SUCCESS('Initial data setup completed!'))

    def create_categories(self):
        """Create initial dataset categories."""
        self.stdout.write('Creating dataset categories...')
        
        categories = [
            {
                'name': 'Computer Vision',
                'slug': 'computer-vision',
                'description': 'Image and video datasets for computer vision tasks',
                'icon': 'fas fa-eye'
            },
            {
                'name': 'Natural Language Processing',
                'slug': 'nlp',
                'description': 'Text datasets for NLP and language modeling',
                'icon': 'fas fa-language'
            },
            {
                'name': 'Time Series',
                'slug': 'time-series',
                'description': 'Sequential data for time series analysis',
                'icon': 'fas fa-chart-line'
            },
            {
                'name': 'Tabular Data',
                'slug': 'tabular',
                'description': 'Structured datasets in tabular format',
                'icon': 'fas fa-table'
            },
            {
                'name': 'Audio',
                'slug': 'audio',
                'description': 'Audio datasets for speech and sound analysis',
                'icon': 'fas fa-volume-up'
            },
            {
                'name': 'Healthcare',
                'slug': 'healthcare',
                'description': 'Medical and healthcare datasets',
                'icon': 'fas fa-heartbeat'
            },
            {
                'name': 'Finance',
                'slug': 'finance',
                'description': 'Financial and economic datasets',
                'icon': 'fas fa-chart-bar'
            },
            {
                'name': 'Social Media',
                'slug': 'social-media',
                'description': 'Social media and web scraping datasets',
                'icon': 'fas fa-share-alt'
            }
        ]

        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'  Created category: {category.name}')

    def create_tags(self):
        """Create initial tags."""
        self.stdout.write('Creating tags...')
        
        tags = [
            {'name': 'Classification', 'slug': 'classification', 'color': '#007bff'},
            {'name': 'Regression', 'slug': 'regression', 'color': '#28a745'},
            {'name': 'Clustering', 'slug': 'clustering', 'color': '#ffc107'},
            {'name': 'Deep Learning', 'slug': 'deep-learning', 'color': '#dc3545'},
            {'name': 'Supervised', 'slug': 'supervised', 'color': '#6f42c1'},
            {'name': 'Unsupervised', 'slug': 'unsupervised', 'color': '#fd7e14'},
            {'name': 'Reinforcement Learning', 'slug': 'reinforcement-learning', 'color': '#20c997'},
            {'name': 'Large Dataset', 'slug': 'large-dataset', 'color': '#6c757d'},
            {'name': 'Clean Data', 'slug': 'clean-data', 'color': '#198754'},
            {'name': 'Raw Data', 'slug': 'raw-data', 'color': '#e63946'},
        ]

        for tag_data in tags:
            tag, created = Tag.objects.get_or_create(
                slug=tag_data['slug'],
                defaults=tag_data
            )
            if created:
                self.stdout.write(f'  Created tag: {tag.name}')

    def create_ml_algorithms(self):
        """Create initial ML algorithms."""
        self.stdout.write('Creating ML algorithms...')
        
        algorithms = [
            {
                'name': 'Logistic Regression',
                'slug': 'logistic-regression',
                'algorithm_type': 'classification',
                'description': 'Linear model for binary and multiclass classification',
                'library': 'scikit-learn',
                'class_name': 'LogisticRegression',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'C': {'type': 'number', 'default': 1.0, 'minimum': 0.001},
                        'max_iter': {'type': 'integer', 'default': 100, 'minimum': 1},
                        'solver': {'type': 'string', 'enum': ['liblinear', 'lbfgs'], 'default': 'lbfgs'}
                    }
                },
                'default_parameters': {'C': 1.0, 'max_iter': 100, 'solver': 'lbfgs'},
                'cost_per_hour': Decimal('0.01000000')
            },
            {
                'name': 'Random Forest',
                'slug': 'random-forest',
                'algorithm_type': 'classification',
                'description': 'Ensemble method using multiple decision trees',
                'library': 'scikit-learn',
                'class_name': 'RandomForestClassifier',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'n_estimators': {'type': 'integer', 'default': 100, 'minimum': 1},
                        'max_depth': {'type': 'integer', 'default': None, 'minimum': 1},
                        'min_samples_split': {'type': 'integer', 'default': 2, 'minimum': 2}
                    }
                },
                'default_parameters': {'n_estimators': 100, 'max_depth': None, 'min_samples_split': 2},
                'cost_per_hour': Decimal('0.02000000')
            },
            {
                'name': 'Linear Regression',
                'slug': 'linear-regression',
                'algorithm_type': 'regression',
                'description': 'Linear model for regression tasks',
                'library': 'scikit-learn',
                'class_name': 'LinearRegression',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'fit_intercept': {'type': 'boolean', 'default': True},
                        'normalize': {'type': 'boolean', 'default': False}
                    }
                },
                'default_parameters': {'fit_intercept': True, 'normalize': False},
                'cost_per_hour': Decimal('0.01000000')
            },
            {
                'name': 'K-Means Clustering',
                'slug': 'kmeans',
                'algorithm_type': 'clustering',
                'description': 'Unsupervised clustering algorithm',
                'library': 'scikit-learn',
                'class_name': 'KMeans',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'n_clusters': {'type': 'integer', 'default': 8, 'minimum': 2},
                        'max_iter': {'type': 'integer', 'default': 300, 'minimum': 1},
                        'n_init': {'type': 'integer', 'default': 10, 'minimum': 1}
                    }
                },
                'default_parameters': {'n_clusters': 8, 'max_iter': 300, 'n_init': 10},
                'cost_per_hour': Decimal('0.01500000')
            },
            {
                'name': 'Support Vector Machine',
                'slug': 'svm',
                'algorithm_type': 'classification',
                'description': 'Support Vector Machine for classification',
                'library': 'scikit-learn',
                'class_name': 'SVC',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'C': {'type': 'number', 'default': 1.0, 'minimum': 0.001},
                        'kernel': {'type': 'string', 'enum': ['linear', 'poly', 'rbf', 'sigmoid'], 'default': 'rbf'},
                        'gamma': {'type': 'string', 'enum': ['scale', 'auto'], 'default': 'scale'}
                    }
                },
                'default_parameters': {'C': 1.0, 'kernel': 'rbf', 'gamma': 'scale'},
                'cost_per_hour': Decimal('0.03000000')
            }
        ]

        for alg_data in algorithms:
            algorithm, created = MLAlgorithm.objects.get_or_create(
                slug=alg_data['slug'],
                defaults=alg_data
            )
            if created:
                self.stdout.write(f'  Created algorithm: {algorithm.name}')

    def create_compute_resources(self):
        """Create initial compute resources."""
        self.stdout.write('Creating compute resources...')
        
        resources = [
            {
                'name': 'CPU-Small',
                'description': 'Small CPU instance for light ML tasks',
                'cpu_cores': 2,
                'memory_gb': 4,
                'gpu_count': 0,
                'storage_gb': 50,
                'status': 'available'
            },
            {
                'name': 'CPU-Medium',
                'description': 'Medium CPU instance for moderate ML tasks',
                'cpu_cores': 4,
                'memory_gb': 8,
                'gpu_count': 0,
                'storage_gb': 100,
                'status': 'available'
            },
            {
                'name': 'CPU-Large',
                'description': 'Large CPU instance for heavy ML tasks',
                'cpu_cores': 8,
                'memory_gb': 16,
                'gpu_count': 0,
                'storage_gb': 200,
                'status': 'available'
            },
            {
                'name': 'GPU-Small',
                'description': 'Small GPU instance for deep learning',
                'cpu_cores': 4,
                'memory_gb': 16,
                'gpu_count': 1,
                'gpu_type': 'NVIDIA Tesla T4',
                'storage_gb': 100,
                'status': 'available'
            },
            {
                'name': 'GPU-Large',
                'description': 'Large GPU instance for intensive deep learning',
                'cpu_cores': 8,
                'memory_gb': 32,
                'gpu_count': 2,
                'gpu_type': 'NVIDIA Tesla V100',
                'storage_gb': 500,
                'status': 'available'
            }
        ]

        for res_data in resources:
            resource, created = ComputeResource.objects.get_or_create(
                name=res_data['name'],
                defaults=res_data
            )
            if created:
                self.stdout.write(f'  Created resource: {resource.name}')

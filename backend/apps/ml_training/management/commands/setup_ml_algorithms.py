"""
Management command to set up initial ML algorithms.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from decimal import Decimal
from apps.ml_training.models import MLAlgorithm, ComputeResource


class Command(BaseCommand):
    help = 'Set up initial ML algorithms and compute resources'

    def handle(self, *args, **options):
        self.stdout.write('Setting up ML algorithms...')
        
        # Classification algorithms
        algorithms_data = [
            {
                'name': 'Logistic Regression',
                'algorithm_type': 'classification',
                'description': 'Linear model for binary and multiclass classification problems.',
                'library': 'scikit-learn',
                'class_name': 'logistic_regression',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'C': {'type': 'number', 'default': 1.0, 'minimum': 0.001},
                        'max_iter': {'type': 'integer', 'default': 100, 'minimum': 1},
                        'solver': {
                            'type': 'string',
                            'enum': ['liblinear', 'lbfgs', 'newton-cg', 'sag', 'saga'],
                            'default': 'lbfgs'
                        }
                    }
                },
                'default_parameters': {
                    'C': 1.0,
                    'max_iter': 100,
                    'solver': 'lbfgs',
                    'random_state': 42
                },
                'min_memory_mb': 512,
                'min_cpu_cores': 1,
                'supports_gpu': False,
                'cost_per_hour': Decimal('0.01000000')
            },
            {
                'name': 'Random Forest Classifier',
                'algorithm_type': 'classification',
                'description': 'Ensemble method using multiple decision trees for classification.',
                'library': 'scikit-learn',
                'class_name': 'random_forest_classifier',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'n_estimators': {'type': 'integer', 'default': 100, 'minimum': 1},
                        'max_depth': {'type': 'integer', 'default': None, 'minimum': 1},
                        'min_samples_split': {'type': 'integer', 'default': 2, 'minimum': 2},
                        'min_samples_leaf': {'type': 'integer', 'default': 1, 'minimum': 1}
                    }
                },
                'default_parameters': {
                    'n_estimators': 100,
                    'max_depth': None,
                    'min_samples_split': 2,
                    'min_samples_leaf': 1,
                    'random_state': 42
                },
                'min_memory_mb': 1024,
                'min_cpu_cores': 2,
                'supports_gpu': False,
                'cost_per_hour': Decimal('0.02000000')
            },
            {
                'name': 'Support Vector Machine',
                'algorithm_type': 'classification',
                'description': 'Support Vector Machine for classification with various kernel functions.',
                'library': 'scikit-learn',
                'class_name': 'svm_classifier',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'C': {'type': 'number', 'default': 1.0, 'minimum': 0.001},
                        'kernel': {
                            'type': 'string',
                            'enum': ['linear', 'poly', 'rbf', 'sigmoid'],
                            'default': 'rbf'
                        },
                        'gamma': {
                            'type': 'string',
                            'enum': ['scale', 'auto'],
                            'default': 'scale'
                        }
                    }
                },
                'default_parameters': {
                    'C': 1.0,
                    'kernel': 'rbf',
                    'gamma': 'scale',
                    'random_state': 42
                },
                'min_memory_mb': 1024,
                'min_cpu_cores': 2,
                'supports_gpu': False,
                'cost_per_hour': Decimal('0.03000000')
            },
            
            # Regression algorithms
            {
                'name': 'Linear Regression',
                'algorithm_type': 'regression',
                'description': 'Linear regression model for continuous target variables.',
                'library': 'scikit-learn',
                'class_name': 'linear_regression',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'fit_intercept': {'type': 'boolean', 'default': True}
                    }
                },
                'default_parameters': {
                    'fit_intercept': True
                },
                'min_memory_mb': 512,
                'min_cpu_cores': 1,
                'supports_gpu': False,
                'cost_per_hour': Decimal('0.01000000')
            },
            {
                'name': 'Random Forest Regressor',
                'algorithm_type': 'regression',
                'description': 'Ensemble method using multiple decision trees for regression.',
                'library': 'scikit-learn',
                'class_name': 'random_forest_regressor',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'n_estimators': {'type': 'integer', 'default': 100, 'minimum': 1},
                        'max_depth': {'type': 'integer', 'default': None, 'minimum': 1},
                        'min_samples_split': {'type': 'integer', 'default': 2, 'minimum': 2},
                        'min_samples_leaf': {'type': 'integer', 'default': 1, 'minimum': 1}
                    }
                },
                'default_parameters': {
                    'n_estimators': 100,
                    'max_depth': None,
                    'min_samples_split': 2,
                    'min_samples_leaf': 1,
                    'random_state': 42
                },
                'min_memory_mb': 1024,
                'min_cpu_cores': 2,
                'supports_gpu': False,
                'cost_per_hour': Decimal('0.02000000')
            },
            {
                'name': 'Support Vector Regression',
                'algorithm_type': 'regression',
                'description': 'Support Vector Machine for regression problems.',
                'library': 'scikit-learn',
                'class_name': 'svm_regressor',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'C': {'type': 'number', 'default': 1.0, 'minimum': 0.001},
                        'kernel': {
                            'type': 'string',
                            'enum': ['linear', 'poly', 'rbf', 'sigmoid'],
                            'default': 'rbf'
                        },
                        'gamma': {
                            'type': 'string',
                            'enum': ['scale', 'auto'],
                            'default': 'scale'
                        }
                    }
                },
                'default_parameters': {
                    'C': 1.0,
                    'kernel': 'rbf',
                    'gamma': 'scale'
                },
                'min_memory_mb': 1024,
                'min_cpu_cores': 2,
                'supports_gpu': False,
                'cost_per_hour': Decimal('0.03000000')
            },
            
            # Clustering algorithms
            {
                'name': 'K-Means Clustering',
                'algorithm_type': 'clustering',
                'description': 'K-means clustering algorithm for unsupervised learning.',
                'library': 'scikit-learn',
                'class_name': 'kmeans',
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'n_clusters': {'type': 'integer', 'default': 8, 'minimum': 2},
                        'init': {
                            'type': 'string',
                            'enum': ['k-means++', 'random'],
                            'default': 'k-means++'
                        },
                        'max_iter': {'type': 'integer', 'default': 300, 'minimum': 1},
                        'tol': {'type': 'number', 'default': 0.0001, 'minimum': 0.0001}
                    }
                },
                'default_parameters': {
                    'n_clusters': 8,
                    'init': 'k-means++',
                    'max_iter': 300,
                    'tol': 0.0001,
                    'random_state': 42
                },
                'min_memory_mb': 512,
                'min_cpu_cores': 1,
                'supports_gpu': False,
                'cost_per_hour': Decimal('0.01500000')
            }
        ]
        
        created_count = 0
        for algo_data in algorithms_data:
            slug = slugify(algo_data['name'])
            algorithm, created = MLAlgorithm.objects.get_or_create(
                slug=slug,
                defaults={**algo_data, 'slug': slug}
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  Created algorithm: {algorithm.name}')
            else:
                self.stdout.write(f'  Algorithm exists: {algorithm.name}')
        
        self.stdout.write(f'Created {created_count} new algorithms')
        
        # Create compute resources
        self.stdout.write('\nSetting up compute resources...')
        
        compute_resources = [
            {
                'name': 'CPU Worker 1',
                'description': 'General purpose CPU worker for ML training',
                'cpu_cores': 4,
                'memory_gb': 8,
                'gpu_count': 0,
                'gpu_type': '',
                'storage_gb': 100,
                'status': 'available'
            },
            {
                'name': 'CPU Worker 2',
                'description': 'High-memory CPU worker for large datasets',
                'cpu_cores': 8,
                'memory_gb': 16,
                'gpu_count': 0,
                'gpu_type': '',
                'storage_gb': 200,
                'status': 'available'
            },
            {
                'name': 'GPU Worker 1',
                'description': 'GPU-enabled worker for deep learning',
                'cpu_cores': 8,
                'memory_gb': 32,
                'gpu_count': 1,
                'gpu_type': 'NVIDIA RTX 4090',
                'storage_gb': 500,
                'status': 'available'
            }
        ]
        
        resource_count = 0
        for resource_data in compute_resources:
            resource, created = ComputeResource.objects.get_or_create(
                name=resource_data['name'],
                defaults=resource_data
            )
            
            if created:
                resource_count += 1
                self.stdout.write(f'  Created resource: {resource.name}')
            else:
                self.stdout.write(f'  Resource exists: {resource.name}')
        
        self.stdout.write(f'Created {resource_count} new compute resources')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully set up ML training infrastructure:\n'
                f'  - {MLAlgorithm.objects.count()} algorithms available\n'
                f'  - {ComputeResource.objects.count()} compute resources available'
            )
        )

"""
Celery tasks for ML Training app.
"""
import os
import json
import joblib
import pandas as pd
import numpy as np
import psutil
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from celery import shared_task
import logging
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.svm import SVC, SVR
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

from .models import TrainingJob, TrainedModel, ModelInference, TrainingQueue, ComputeResource
from apps.datasets.models import Dataset

logger = logging.getLogger(__name__)

# Algorithm mapping
ALGORITHM_CLASSES = {
    'logistic_regression': LogisticRegression,
    'linear_regression': LinearRegression,
    'random_forest_classifier': RandomForestClassifier,
    'random_forest_regressor': RandomForestRegressor,
    'svm_classifier': SVC,
    'svm_regressor': SVR,
    'kmeans': KMeans,
}


@shared_task(bind=True, max_retries=3)
def start_training_job(self, training_job_id):
    """
    Start a training job.
    
    Args:
        training_job_id: ID of the training job to start
    """
    try:
        training_job = TrainingJob.objects.get(id=training_job_id)
        
        logger.info(f"Starting training job: {training_job.name}")
        
        # Add to queue
        queue_position = TrainingQueue.objects.count() + 1
        queue_entry, created = TrainingQueue.objects.get_or_create(
            training_job=training_job,
            defaults={'queue_position': queue_position}
        )
        
        # Update job status
        training_job.status = 'queued'
        training_job.save()
        
        # Check for available compute resources
        available_resource = ComputeResource.objects.filter(
            status='available',
            cpu_cores__gte=training_job.cpu_cores,
            memory_gb__gte=training_job.memory_limit_mb // 1024
        ).first()
        
        if available_resource:
            # Assign resource and start training
            available_resource.status = 'busy'
            available_resource.current_job = training_job
            available_resource.save()
            
            # Remove from queue
            queue_entry.delete()
            
            # Start actual training
            execute_training_job.delay(training_job_id)
        else:
            logger.info(f"No available resources. Job {training_job.name} queued at position {queue_position}")
        
    except TrainingJob.DoesNotExist:
        logger.error(f"Training job not found: {training_job_id}")
    except Exception as e:
        logger.error(f"Error starting training job {training_job_id}: {str(e)}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=1)
def execute_training_job(self, training_job_id):
    """
    Execute the actual ML training.
    
    Args:
        training_job_id: ID of the training job to execute
    """
    import sys
    
    # Set a reasonable recursion limit to prevent infinite recursion
    original_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(1000)
    
    training_job = None
    start_time = timezone.now()
    peak_memory_mb = 0
    
    try:
        process = psutil.Process()
    except Exception as e:
        logger.error(f"Failed to initialize psutil process: {e}")
        process = None
    
    try:
        training_job = TrainingJob.objects.get(id=training_job_id)
        
        logger.info(f"Executing training job: {training_job.name}")
        
        # Update job status
        training_job.status = 'running'
        training_job.started_at = start_time
        training_job.progress_percentage = 0
        training_job.save()
        
        # Track initial memory usage
        if process:
            try:
                initial_memory = process.memory_info().rss / 1024 / 1024  # Convert to MB
                peak_memory_mb = initial_memory
            except Exception as e:
                logger.warning(f"Failed to get initial memory: {e}")
                peak_memory_mb = 0
        else:
            peak_memory_mb = 0
        
        def update_peak_memory():
            nonlocal peak_memory_mb
            if not process:
                return
            try:
                current_memory = process.memory_info().rss / 1024 / 1024
                if current_memory > peak_memory_mb:
                    peak_memory_mb = current_memory
            except Exception as e:
                logger.warning(f"Failed to track memory usage: {e}")
        
        # Load dataset
        dataset = training_job.dataset
        if not dataset.file:
            raise ValueError("Dataset file not found")
        
        # Read dataset based on file type
        file_path = dataset.file.path
        if dataset.file_type == 'csv':
            df = pd.read_csv(file_path)
        elif dataset.file_type == 'json':
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {dataset.file_type}")
        
        training_job.progress_percentage = 20
        training_job.training_logs += f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns\n"
        training_job.save()
        
        # Track memory after data loading
        update_peak_memory()
        
        # Prepare data based on algorithm type
        algorithm = training_job.algorithm
        algorithm_class = ALGORITHM_CLASSES.get(algorithm.class_name)
        
        if not algorithm_class:
            raise ValueError(f"Algorithm not implemented: {algorithm.class_name}")
        
        # Basic data preprocessing
        # Remove non-numeric columns for now (simplified)
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            raise ValueError("No numeric columns found in dataset")
        
        training_job.progress_percentage = 40
        training_job.training_logs += f"Preprocessed data: {numeric_df.shape[1]} numeric features\n"
        training_job.save()
        
        # Track memory after preprocessing
        update_peak_memory()
        
        # Prepare features and target
        if algorithm.algorithm_type in ['classification', 'regression']:
            # Assume last column is target
            X = numeric_df.iloc[:, :-1]
            y = numeric_df.iloc[:, -1]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, 
                test_size=1 - training_job.train_test_split,
                random_state=training_job.random_seed
            )
            
        elif algorithm.algorithm_type == 'clustering':
            # Use all features for clustering
            X = numeric_df
            X_train = X
            
        training_job.progress_percentage = 60
        training_job.training_logs += f"Data split completed\n"
        training_job.save()
        
        # Track memory after data splitting
        update_peak_memory()
        
        # Initialize and train model
        model_params = training_job.parameters or algorithm.default_parameters
        model = algorithm_class(**model_params)
        
        if algorithm.algorithm_type in ['classification', 'regression']:
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            metrics = {}
            if algorithm.algorithm_type == 'classification':
                metrics['accuracy'] = float(accuracy_score(y_test, y_pred))
                metrics['precision'] = float(precision_score(y_test, y_pred, average='weighted'))
                metrics['recall'] = float(recall_score(y_test, y_pred, average='weighted'))
                metrics['f1_score'] = float(f1_score(y_test, y_pred, average='weighted'))
            else:  # regression
                from sklearn.metrics import mean_squared_error, r2_score
                metrics['mse'] = float(mean_squared_error(y_test, y_pred))
                metrics['r2_score'] = float(r2_score(y_test, y_pred))
                
        elif algorithm.algorithm_type == 'clustering':
            model.fit(X_train)
            
            # Calculate clustering metrics
            from sklearn.metrics import silhouette_score
            labels = model.predict(X_train)
            metrics = {
                'silhouette_score': float(silhouette_score(X_train, labels)),
                'n_clusters': int(model.n_clusters)
            }
        
        training_job.progress_percentage = 80
        training_job.training_logs += f"Model training completed\n"
        training_job.model_metrics = metrics
        training_job.save()
        
        # Track memory after model training
        update_peak_memory()
        
        # Save trained model
        model_filename = f"model_{training_job.id}_{int(timezone.now().timestamp())}.pkl"
        model_path = os.path.join(settings.MEDIA_ROOT, 'trained_models', model_filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Save model using joblib
        joblib.dump(model, model_path)
        
        # Update training job with proper FileField
        from django.core.files import File
        with open(model_path, 'rb') as f:
            training_job.model_file.save(model_filename, File(f), save=False)
        training_job.progress_percentage = 100
        training_job.status = 'completed'
        training_job.completed_at = timezone.now()
        
        # Calculate actual runtime and cost
        runtime_seconds = (training_job.completed_at - training_job.started_at).total_seconds()
        training_job.actual_runtime_seconds = int(runtime_seconds)
        training_job.actual_cost = training_job.calculate_cost()
        
        # Update peak memory one final time and save it
        update_peak_memory()
        training_job.peak_memory_usage_mb = int(peak_memory_mb)
        
        training_job.training_logs += f"Training completed successfully\n"
        training_job.training_logs += f"Runtime: {runtime_seconds:.2f} seconds\n"
        training_job.training_logs += f"Peak Memory: {peak_memory_mb:.1f} MB\n"
        training_job.training_logs += f"Cost: {training_job.actual_cost} NRC\n"
        training_job.save()
        
        # Create trained model record
        trained_model = TrainedModel.objects.create(
            name=f"{training_job.name} - Trained Model",
            description=f"Model trained from {training_job.name}",
            owner=training_job.user,
            training_job=training_job,
            algorithm=training_job.algorithm,
            source_dataset=training_job.dataset,
            model_file=training_job.model_file,
            model_size_bytes=os.path.getsize(model_path),
            model_format='joblib',
            metrics=metrics,
            accuracy=metrics.get('accuracy'),
            precision=metrics.get('precision'),
            recall=metrics.get('recall'),
            f1_score=metrics.get('f1_score')
        )
        
        # Generate visualization
        try:
            generate_training_visualization(training_job_id)  # Call directly instead of async
        except Exception as e:
            logger.warning(f"Failed to generate visualization: {e}")
        
        # Log blockchain transaction (temporarily disabled to prevent recursion)  
        # log_training_to_blockchain.delay(training_job_id)
        
        logger.info(f"Training job completed: {training_job.name}")
        
    except Exception as e:
        logger.error(f"Error executing training job {training_job_id}: {str(e)}")
        
        if training_job:
            training_job.status = 'failed'
            training_job.completed_at = timezone.now()
            training_job.error_message = str(e)
            training_job.training_logs += f"ERROR: {str(e)}\n"
            
            # Calculate runtime even for failed jobs
            if training_job.started_at:
                runtime_seconds = (training_job.completed_at - training_job.started_at).total_seconds()
                training_job.actual_runtime_seconds = int(runtime_seconds)
            
            training_job.save()
        
        # Retry once for transient errors
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300)  # Retry after 5 minutes
    
    finally:
        # Restore original recursion limit
        sys.setrecursionlimit(original_limit)
        
        # Release compute resource
        if training_job:
            resource = ComputeResource.objects.filter(current_job=training_job).first()
            if resource:
                resource.status = 'available'
                resource.current_job = None
                resource.last_used_at = timezone.now()
                resource.total_jobs_completed += 1
                if training_job.actual_runtime_seconds:
                    resource.total_runtime_hours += Decimal(str(training_job.actual_runtime_seconds / 3600))
                resource.save()
            
            # Process next job in queue (temporarily disabled to prevent recursion)
            # process_training_queue.delay()


@shared_task
def generate_training_visualization(training_job_id):
    """
    Generate visualization for training results.
    
    Args:
        training_job_id: ID of the training job
    """
    try:
        training_job = TrainingJob.objects.get(id=training_job_id)
        
        if not training_job.model_metrics:
            return
        
        # Create visualization based on algorithm type
        plt.figure(figsize=(10, 6))
        
        if training_job.algorithm.algorithm_type == 'classification':
            metrics = training_job.model_metrics
            metric_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
            metric_values = [
                metrics.get('accuracy', 0),
                metrics.get('precision', 0),
                metrics.get('recall', 0),
                metrics.get('f1_score', 0)
            ]
            
            plt.bar(metric_names, metric_values)
            plt.title(f'Classification Metrics - {training_job.name}')
            plt.ylabel('Score')
            plt.ylim(0, 1)
            
        elif training_job.algorithm.algorithm_type == 'regression':
            # Simple metrics display for regression
            metrics = training_job.model_metrics
            plt.text(0.5, 0.7, f"MSE: {metrics.get('mse', 0):.4f}", 
                    transform=plt.gca().transAxes, fontsize=14, ha='center')
            plt.text(0.5, 0.5, f"R² Score: {metrics.get('r2_score', 0):.4f}", 
                    transform=plt.gca().transAxes, fontsize=14, ha='center')
            plt.title(f'Regression Metrics - {training_job.name}')
            plt.axis('off')
            
        elif training_job.algorithm.algorithm_type == 'clustering':
            # Clustering metrics display
            metrics = training_job.model_metrics
            plt.text(0.5, 0.7, f"Silhouette Score: {metrics.get('silhouette_score', 0):.4f}", 
                    transform=plt.gca().transAxes, fontsize=16, ha='center', fontweight='bold')
            plt.text(0.5, 0.5, f"Number of Clusters: {metrics.get('n_clusters', 0)}", 
                    transform=plt.gca().transAxes, fontsize=14, ha='center')
            plt.text(0.5, 0.3, f"Algorithm: {training_job.algorithm.name}", 
                    transform=plt.gca().transAxes, fontsize=12, ha='center', style='italic')
            plt.title(f'Clustering Results - {training_job.name}')
            plt.axis('off')
        
        # Save plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        # Update training job with visualization
        training_job.model_metrics['visualization'] = plot_data
        training_job.save()
        
        logger.info(f"Generated visualization for training job: {training_job.name}")
        
    except Exception as e:
        logger.error(f"Error generating visualization for job {training_job_id}: {str(e)}")


@shared_task
def run_model_inference(inference_id):
    """
    Run inference on a trained model.
    
    Args:
        inference_id: ID of the model inference request
    """
    try:
        inference = ModelInference.objects.get(id=inference_id)
        start_time = timezone.now()
        
        inference.status = 'processing'
        inference.save()
        
        # Load the trained model
        model_path = inference.model.model_file.path
        model = joblib.load(model_path)
        
        # Prepare input data
        input_data = inference.input_data
        
        if isinstance(input_data, dict) and 'features' in input_data:
            # Convert to numpy array
            features = np.array(input_data['features']).reshape(1, -1)
        else:
            raise ValueError("Invalid input data format")
        
        # Make prediction
        prediction = model.predict(features)
        
        # Get confidence scores if available
        confidence_scores = {}
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(features)
            confidence_scores = {
                'probabilities': proba[0].tolist(),
                'classes': model.classes_.tolist() if hasattr(model, 'classes_') else []
            }
        
        # Update inference record
        inference.predictions = {
            'prediction': prediction.tolist(),
            'input_shape': features.shape
        }
        inference.confidence_scores = confidence_scores
        inference.status = 'completed'
        inference.completed_at = timezone.now()
        inference.processing_time_ms = int((inference.completed_at - start_time).total_seconds() * 1000)
        inference.save()
        
        logger.info(f"Inference completed for model: {inference.model.name}")
        
    except Exception as e:
        logger.error(f"Error running inference {inference_id}: {str(e)}")
        
        try:
            inference = ModelInference.objects.get(id=inference_id)
            inference.status = 'failed'
            inference.error_message = str(e)
            inference.completed_at = timezone.now()
            inference.save()
        except:
            pass


@shared_task
def process_training_queue():
    """
    Process the training queue and start next available job.
    """
    try:
        # Get next job in queue
        next_queue_entry = TrainingQueue.objects.order_by('queue_position').first()
        
        if not next_queue_entry:
            return
        
        training_job = next_queue_entry.training_job
        
        # Check for available compute resources
        available_resource = ComputeResource.objects.filter(
            status='available',
            cpu_cores__gte=training_job.cpu_cores,
            memory_gb__gte=training_job.memory_limit_mb // 1024
        ).first()
        
        if available_resource:
            # Assign resource and start training
            available_resource.status = 'busy'
            available_resource.current_job = training_job
            available_resource.save()
            
            # Remove from queue
            next_queue_entry.delete()
            
            # Start training
            execute_training_job.delay(str(training_job.id))
            
            logger.info(f"Started queued training job: {training_job.name}")
        
    except Exception as e:
        logger.error(f"Error processing training queue: {str(e)}")


@shared_task
def log_training_to_blockchain(training_job_id):
    """
    Log training job results to blockchain.
    
    Args:
        training_job_id: ID of the training job
    """
    try:
        training_job = TrainingJob.objects.get(id=training_job_id)
        
        # Import Web3 utilities
        from django.conf import settings
        from web3 import Web3
        import json
        
        # Check if blockchain logging is enabled
        if not hasattr(settings, 'BLOCKCHAIN_SETTINGS') or not settings.BLOCKCHAIN_SETTINGS.get('ENABLED'):
            logger.info("Blockchain logging disabled")
            return
        
        # Connect to blockchain
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_SETTINGS['RPC_URL']))
        
        if not w3.is_connected():
            logger.error("Failed to connect to blockchain")
            return
        
        # Load contract ABI and address
        ml_logger_address = settings.BLOCKCHAIN_SETTINGS.get('ML_LOGGER_CONTRACT_ADDRESS')
        if not ml_logger_address:
            logger.error("ML Logger contract address not configured")
            return
        
        # Contract ABI (simplified for key functions)
        ml_logger_abi = [
            {
                "inputs": [
                    {"name": "_backendJobId", "type": "string"},
                    {"name": "_modelHash", "type": "string"},
                    {"name": "_metricsHash", "type": "string"},
                    {"name": "_actualCost", "type": "uint256"}
                ],
                "name": "completeTrainingJob",
                "outputs": [],
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "_backendJobId", "type": "string"},
                    {"name": "_accuracy", "type": "uint256"},
                    {"name": "_precision", "type": "uint256"},
                    {"name": "_recall", "type": "uint256"},
                    {"name": "_f1Score", "type": "uint256"},
                    {"name": "_trainingTime", "type": "uint256"},
                    {"name": "_memoryUsed", "type": "uint256"},
                    {"name": "_additionalMetrics", "type": "string"}
                ],
                "name": "recordMetrics",
                "outputs": [],
                "type": "function"
            }
        ]
        
        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(ml_logger_address),
            abi=ml_logger_abi
        )
        
        # Get account for transactions
        account = w3.eth.account.from_key(settings.BLOCKCHAIN_SETTINGS['PRIVATE_KEY'])
        
        # Prepare transaction data
        backend_job_id = str(training_job.id)
        model_hash = training_job.model_file.name if training_job.model_file else ""
        metrics_hash = ""  # Could be IPFS hash of detailed metrics
        actual_cost = int(float(training_job.actual_cost or 0) * 10**18)  # Convert to wei
        
        # Complete training job on blockchain
        if training_job.status == 'completed':
            tx_data = contract.functions.completeTrainingJob(
                backend_job_id,
                model_hash,
                metrics_hash,
                actual_cost
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': w3.to_wei('20', 'gwei')
            })
            
            # Sign and send transaction
            signed_tx = w3.eth.account.sign_transaction(tx_data, settings.BLOCKCHAIN_SETTINGS['PRIVATE_KEY'])
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Training job completion logged to blockchain: {tx_hash.hex()}")
            
            # Record metrics if available
            if training_job.model_metrics:
                metrics = training_job.model_metrics
                
                # Scale metrics to integers (multiply by 10000 for percentage precision)
                accuracy = int((metrics.get('accuracy', 0) * 10000))
                precision = int((metrics.get('precision', 0) * 10000))
                recall = int((metrics.get('recall', 0) * 10000))
                f1_score = int((metrics.get('f1_score', 0) * 10000))
                training_time = training_job.actual_runtime_seconds or 0
                memory_used = training_job.peak_memory_usage_mb or 0
                additional_metrics = json.dumps({
                    k: v for k, v in metrics.items() 
                    if k not in ['accuracy', 'precision', 'recall', 'f1_score']
                })
                
                metrics_tx_data = contract.functions.recordMetrics(
                    backend_job_id,
                    accuracy,
                    precision,
                    recall,
                    f1_score,
                    training_time,
                    memory_used,
                    additional_metrics
                ).build_transaction({
                    'from': account.address,
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'gas': 150000,
                    'gasPrice': w3.to_wei('20', 'gwei')
                })
                
                signed_metrics_tx = w3.eth.account.sign_transaction(
                    metrics_tx_data, 
                    settings.BLOCKCHAIN_SETTINGS['PRIVATE_KEY']
                )
                metrics_tx_hash = w3.eth.send_raw_transaction(signed_metrics_tx.rawTransaction)
                
                logger.info(f"Training metrics logged to blockchain: {metrics_tx_hash.hex()}")
        
        logger.info(f"Blockchain logging completed for training job: {training_job.name}")
        
    except Exception as e:
        logger.error(f"Error logging training job {training_job_id} to blockchain: {str(e)}")


@shared_task
def cleanup_old_training_files():
    """
    Clean up old training files and models.
    """
    try:
        from datetime import timedelta
        
        # Find old failed training jobs (older than 7 days)
        cutoff_date = timezone.now() - timedelta(days=7)
        old_failed_jobs = TrainingJob.objects.filter(
            status='failed',
            completed_at__lt=cutoff_date
        )
        
        cleaned_count = 0
        for job in old_failed_jobs:
            if job.model_file:
                try:
                    job.model_file.delete(save=False)
                    cleaned_count += 1
                except Exception as e:
                    logger.error(f"Error deleting file for job {job.id}: {str(e)}")
        
        logger.info(f"Cleaned up {cleaned_count} old training files")
        
    except Exception as e:
        logger.error(f"Error during training file cleanup: {str(e)}")


@shared_task
def update_training_statistics():
    """
    Update training statistics and metrics.
    """
    try:
        # Update algorithm usage statistics
        from django.db.models import Count
        
        algorithms = MLAlgorithm.objects.annotate(
            usage_count=Count('training_jobs')
        )
        
        for algorithm in algorithms:
            # Could store usage statistics in a separate model
            pass
        
        logger.info("Updated training statistics")
        
    except Exception as e:
        logger.error(f"Error updating training statistics: {str(e)}")

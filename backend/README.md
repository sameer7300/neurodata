# NeuroData Backend

A comprehensive Django backend for the NeuroData decentralized data marketplace with integrated ML training capabilities.

## 🚀 Features

### Core Functionality
- **User Authentication**: Custom user model with wallet integration
- **Dataset Management**: Upload, categorize, and manage datasets
- **Marketplace**: Buy/sell datasets with blockchain payments
- **ML Training**: Train ML models on purchased datasets
- **Decentralized Storage**: IPFS integration for dataset storage
- **Blockchain Integration**: Web3.py for Ethereum/Polygon transactions

### Technical Stack
- **Backend**: Django 4.2 + Django REST Framework
- **Database**: PostgreSQL with connection pooling
- **Caching**: Redis for sessions and background tasks
- **Background Jobs**: Celery + Redis
- **Blockchain**: Web3.py for smart contract interaction
- **Storage**: IPFS for decentralized file storage
- **ML**: Scikit-learn, Pandas, NumPy

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (for IPFS)

## 🛠️ Quick Setup

### 1. Clone and Setup Environment

```bash
cd backend
python setup.py
```

This will:
- Create virtual environment
- Install dependencies
- Create .env file from template
- Setup directory structure

### 2. Configure Environment

Update `.env` file with your settings:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/neurodata

# Redis
REDIS_URL=redis://localhost:6379/0

# Blockchain
WEB3_PROVIDER_URL=https://polygon-mainnet.infura.io/v3/YOUR_PROJECT_ID
PRIVATE_KEY=your_private_key_here

# IPFS
IPFS_API_URL=http://localhost:5001
IPFS_GATEWAY_URL=http://localhost:8080

# Security
SECRET_KEY=your_secret_key_here
DEBUG=True
```

### 3. Database Setup

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Setup initial data
python manage.py setup_initial_data
```

### 4. Start Services

```bash
# Start Django development server
python manage.py runserver

# Start Celery worker (in another terminal)
celery -A neurodata worker -l info

# Start Celery beat (in another terminal)
celery -A neurodata beat -l info
```

## 📊 Database Models

### Authentication App
- **User**: Extended user model with email authentication
- **UserProfile**: User profiles with wallet addresses and statistics
- **APIKey**: API keys for programmatic access
- **UserActivity**: Activity logging for security and analytics

### Datasets App
- **Dataset**: Core dataset model with IPFS integration
- **Category**: Dataset categorization
- **Tag**: Dataset tagging system
- **DatasetVersion**: Version control for datasets
- **DatasetReview**: User reviews and ratings
- **DatasetAccess**: Access logging
- **DatasetCollection**: User-created dataset collections

### Marketplace App
- **Purchase**: Dataset purchase transactions
- **Transaction**: Blockchain transaction records
- **Escrow**: Secure transaction escrow system
- **Payout**: Seller payout management
- **PlatformFee**: Fee configuration and tracking
- **Refund**: Refund request handling

### ML Training App
- **MLAlgorithm**: Available ML algorithms
- **TrainingJob**: ML training job instances
- **TrainedModel**: Trained models for sharing/selling
- **ModelInference**: Model inference requests
- **TrainingQueue**: Job queue management
- **ComputeResource**: Available compute resources

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile
- `PUT /api/auth/profile/` - Update user profile

### Datasets
- `GET /api/datasets/` - List datasets
- `POST /api/datasets/` - Upload dataset
- `GET /api/datasets/{id}/` - Get dataset details
- `PUT /api/datasets/{id}/` - Update dataset
- `DELETE /api/datasets/{id}/` - Delete dataset
- `POST /api/datasets/{id}/purchase/` - Purchase dataset

### ML Training
- `GET /api/ml/algorithms/` - List available algorithms
- `POST /api/ml/training-jobs/` - Create training job
- `GET /api/ml/training-jobs/` - List training jobs
- `GET /api/ml/training-jobs/{id}/` - Get job details
- `POST /api/ml/models/{id}/inference/` - Run model inference

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.authentication
python manage.py test apps.datasets
python manage.py test apps.marketplace
python manage.py test apps.ml_training

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Run migrations in container
docker-compose exec web python manage.py migrate

# Create superuser in container
docker-compose exec web python manage.py createsuperuser
```

## 📈 Monitoring and Logging

### Health Checks
- `GET /health/` - Basic health check
- `GET /status/` - Detailed system status

### Logging
Logs are stored in the `logs/` directory:
- `django.log` - General Django logs
- `celery.log` - Celery task logs
- `blockchain.log` - Blockchain transaction logs

## 🔐 Security Features

- JWT authentication with refresh tokens
- Rate limiting middleware
- CORS configuration
- Security headers middleware
- API key authentication
- User activity logging
- Input validation and sanitization

## 🚀 Production Deployment

### Environment Variables
Set these in production:
```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=strong-secret-key
```

### Static Files
```bash
python manage.py collectstatic --noinput
```

### Database Optimization
- Enable connection pooling
- Configure read replicas
- Set up database backups

### Caching
- Configure Redis for caching
- Enable template caching
- Use database query optimization

## 📚 API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API docs

## 🔄 Development Workflow

### Making Changes
1. Create a new branch for your feature
2. Make your changes
3. Write/update tests
4. Update documentation
5. Submit a pull request

### Database Migrations
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### Code Quality
```bash
# Format code with Black
black .

# Check code style with flake8
flake8 .

# Sort imports with isort
isort .
```

## 📊 Performance Tips

### Database
- Use select_related() and prefetch_related()
- Add database indexes for frequently queried fields
- Use database connection pooling
- Monitor slow queries

### Caching
- Cache expensive database queries
- Use template fragment caching
- Implement API response caching
- Cache static assets

### Background Tasks
- Use Celery for long-running tasks
- Monitor task queue length
- Set appropriate task timeouts
- Use task retries for reliability

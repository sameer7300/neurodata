# NeuroData: Decentralized Data Marketplace with Built-In ML Training

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 16+](https://img.shields.io/badge/node-16+-green.svg)](https://nodejs.org/)
[![React 19](https://img.shields.io/badge/react-19-blue.svg)](https://reactjs.org/)
[![Django 4.2](https://img.shields.io/badge/django-4.2-green.svg)](https://www.djangoproject.com/)
[![Solidity 0.8.19](https://img.shields.io/badge/solidity-0.8.19-orange.svg)](https://soliditylang.org/)

## 🌟 Overview

NeuroData is a comprehensive decentralized data marketplace that combines blockchain technology, AI/ML capabilities, and secure data trading. Built with Django REST Framework, React TypeScript, and Solidity smart contracts, it provides a complete ecosystem for buying, selling, and training on datasets using the native NeuroCoin (NCR) token.

### 🎯 Key Features

- **🔐 Secure Data Trading**: End-to-end encrypted dataset transactions with escrow protection
- **💰 Native Token Economy**: NeuroCoin (NCR) ERC-20 token with staking rewards
- **🤖 Built-in ML Training**: Train models directly on purchased datasets
- **🛡️ Advanced Escrow System**: Multi-party escrow with dispute resolution
- **🌐 Web3 Integration**: MetaMask wallet authentication and blockchain transactions
- **📊 Comprehensive Dashboard**: Real-time analytics and transaction management
- **🔍 Smart Search**: AI-powered dataset discovery and recommendations
- **⚖️ Dispute Resolution**: Automated and admin-mediated conflict resolution

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │  Blockchain     │
│   React TS      │◄──►│   Django REST   │◄──►│ Smart Contracts │
│   TailwindCSS   │    │   PostgreSQL    │    │   NeuroCoin     │
│   Web3 Context  │    │   Redis Cache   │    │   Escrow Mgmt   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │      IPFS       │
                    │ Dataset Storage │
                    └─────────────────┘
```

### Technology Stack

#### Backend (Django)
- **Framework**: Django 4.2 + Django REST Framework
- **Database**: PostgreSQL with connection pooling
- **Cache**: Redis for sessions and background tasks
- **Background Jobs**: Celery + Redis
- **Blockchain**: Web3.py for Ethereum/Polygon integration
- **Storage**: IPFS for decentralized file storage
- **ML**: Scikit-learn, Pandas, NumPy for model training

#### Frontend (React)
- **Framework**: React 19 with TypeScript
- **Styling**: TailwindCSS with custom design system
- **State Management**: Context API (Web3Context, AuthContext)
- **Routing**: React Router v7 with protected routes
- **Web3**: Ethers.js v6 for blockchain interactions
- **UI Components**: Headless UI + Heroicons
- **Notifications**: React Hot Toast

#### Blockchain (Solidity)
- **Token**: NeuroCoin (NCR) ERC-20 with staking rewards
- **Marketplace**: Dataset trading with escrow protection
- **Escrow Manager**: Advanced multi-party escrow system
- **Network**: Polygon (Mumbai testnet / Mainnet)

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 16+**
- **PostgreSQL 12+**
- **Redis 6+**
- **MetaMask** browser extension

### 1. Clone Repository

```bash
git clone https://github.com/your-username/neuro-chain.git
cd neuro-chain
```

### 2. Backend Setup(private - will be published when the website is fully completed and running)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Setup database
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Setup initial data
python manage.py setup_initial_data

# Start development server
python manage.py runserver
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm start
```

### 4. Smart Contracts Setup

```bash
cd contracts

# Install dependencies
npm install

# Compile contracts
npx hardhat compile

# Deploy to local network
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost
```

## 📋 Environment Configuration

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/neurodata
DB_NAME=neurodata_db
DB_USER=neurodata_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Blockchain
WEB3_PROVIDER_URL=https://polygon-mumbai.g.alchemy.com/v2/YOUR_KEY
PRIVATE_KEY=your_private_key_here
CONTRACT_ADDRESS_NEUROCOIN=0x...
CONTRACT_ADDRESS_MARKETPLACE=0x...

# IPFS
IPFS_API_URL=https://ipfs.infura.io:5001
IPFS_API_KEY=your_api_key
IPFS_API_SECRET=your_api_secret

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

### Frontend (.env.local)

```env
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
REACT_APP_CHAIN_ID=80001
REACT_APP_NETWORK_NAME=Polygon Mumbai
REACT_APP_RPC_URL=https://rpc-mumbai.maticvigil.com
REACT_APP_NEUROCOIN_ADDRESS=0x...
REACT_APP_MARKETPLACE_ADDRESS=0x...
```

## 🔧 Development Workflow

### Backend Development

```bash
# Start services
python manage.py runserver          # Django server
celery -A neurodata worker -l info  # Background tasks
celery -A neurodata beat -l info    # Scheduled tasks

# Database operations
python manage.py makemigrations     # Create migrations
python manage.py migrate            # Apply migrations
python manage.py shell              # Django shell

# Testing
python manage.py test               # Run tests
coverage run --source='.' manage.py test
coverage report                     # Coverage report

# Code quality
black .                            # Format code
flake8 .                          # Check style
isort .                           # Sort imports
```

### Frontend Development

```bash
# Development
npm start                          # Start dev server
npm test                          # Run tests
npm run build                     # Production build

# Code quality
npm run lint                      # ESLint
npm run format                    # Prettier
npm run type-check               # TypeScript check
```

### Smart Contract Development

```bash
# Development
npx hardhat compile               # Compile contracts
npx hardhat test                 # Run tests
npx hardhat node                 # Local blockchain

# Deployment
npx hardhat run scripts/deploy.js --network mumbai
npx hardhat verify --network mumbai CONTRACT_ADDRESS
```

## 📊 Database Schema

### Core Models

#### Authentication
- **User**: Extended user model with email authentication
- **UserProfile**: Profiles with wallet addresses and statistics
- **APIKey**: API keys for programmatic access
- **UserActivity**: Activity logging for security

#### Datasets
- **Dataset**: Core dataset model with IPFS integration
- **Category**: Dataset categorization system
- **Tag**: Flexible tagging system
- **DatasetVersion**: Version control for datasets
- **DatasetReview**: User reviews and ratings
- **DatasetAccess**: Access logging and analytics

#### Marketplace
- **Purchase**: Dataset purchase transactions
- **Transaction**: Blockchain transaction records
- **Escrow**: Advanced escrow system with dispute resolution
- **Payout**: Seller payout management
- **PlatformFee**: Fee configuration and tracking
- **Refund**: Refund request handling

## 🌐 API Documentation

### Authentication Endpoints

```typescript
POST   /auth/login/              // User login
POST   /auth/register/           // User registration
POST   /auth/logout/             // User logout
GET    /auth/user/               // Get user profile
PUT    /auth/profile/            // Update profile
GET    /auth/stats/              // User statistics

// Web3 Authentication
POST   /auth/wallet/connect/     // Connect wallet
POST   /auth/wallet/auth/        // Authenticate with signature
POST   /auth/wallet/link/        // Link wallet to account
```

### Dataset Endpoints

```typescript
GET    /datasets/datasets/       // List datasets
POST   /datasets/datasets/       // Upload dataset
GET    /datasets/datasets/{id}/  // Get dataset details
PUT    /datasets/datasets/{id}/  // Update dataset
DELETE /datasets/datasets/{id}/  // Delete dataset

// Dataset Actions
POST   /datasets/datasets/{id}/purchase/     // Purchase dataset
POST   /datasets/datasets/{id}/favorite/     // Toggle favorite
GET    /datasets/datasets/{id}/download/     // Download dataset
POST   /datasets/datasets/{id}/test_purchase/ // Test purchase

// Search and Discovery
GET    /datasets/search/         // Search datasets
GET    /datasets/categories/     // List categories
GET    /datasets/tags/           // List tags
GET    /datasets/popular/        // Popular datasets
GET    /datasets/featured/       // Featured datasets
```

### Marketplace Endpoints

```typescript
GET    /marketplace/purchases/   // List user purchases
POST   /marketplace/purchases/{id}/ // Update purchase
GET    /marketplace/purchases/{id}/details/ // Purchase details

// Escrow Management
GET    /marketplace/escrows/     // List user escrows
GET    /marketplace/escrows/{id}/ // Get escrow details
POST   /marketplace/escrows/{id}/confirm-receipt/ // Confirm receipt
POST   /marketplace/escrows/{id}/dispute/        // Create dispute
POST   /marketplace/escrows/{id}/auto-release/   // Auto-release funds
```

## 🔐 Security Features

### Authentication & Authorization
- **JWT Authentication**: Secure token-based authentication with refresh
- **Web3 Wallet Auth**: MetaMask signature-based authentication
- **Role-based Permissions**: Granular access control
- **API Rate Limiting**: Protection against abuse
- **CORS Configuration**: Secure cross-origin requests

### Data Protection
- **Input Validation**: Comprehensive data sanitization
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Content Security Policy headers
- **File Upload Security**: Type validation and scanning
- **HTTPS Enforcement**: Secure data transmission

### Blockchain Security
- **Smart Contract Audits**: Comprehensive security reviews
- **Reentrancy Protection**: SafeMath and ReentrancyGuard
- **Access Controls**: Owner and role-based restrictions
- **Emergency Pause**: Circuit breaker functionality

## 🎯 User Flows

### 1. User Registration & Authentication

```mermaid
graph TD
    A[User Visits Site] --> B{Has Account?}
    B -->|No| C[Register with Email]
    B -->|Yes| D[Login]
    C --> E[Verify Email]
    E --> F[Connect MetaMask]
    D --> F
    F --> G[Sign Message]
    G --> H[Dashboard Access]
```

### 2. Dataset Upload & Sale

```mermaid
graph TD
    A[Upload Dataset] --> B[File Validation]
    B --> C[IPFS Storage]
    C --> D[Metadata Creation]
    D --> E[Price Setting]
    E --> F[Category & Tags]
    F --> G[Admin Approval]
    G --> H[Live on Marketplace]
```

### 3. Dataset Purchase & Escrow

```mermaid
graph TD
    A[Browse Datasets] --> B[Select Dataset]
    B --> C[Purchase with NCR]
    C --> D[Escrow Creation]
    D --> E[Seller Delivers]
    E --> F{Buyer Satisfied?}
    F -->|Yes| G[Confirm Receipt]
    F -->|No| H[Open Dispute]
    G --> I[Release Payment]
    H --> J[Admin Resolution]
    J --> I
```

## 🔧 Advanced Features

### Escrow System
- **Multi-party Escrow**: Buyer, seller, and arbitrator involvement
- **Milestone-based Releases**: Gradual payment releases
- **Automated Dispute Resolution**: Community voting system
- **Emergency Recovery**: Admin intervention capabilities
- **Fee Distribution**: Transparent fee handling

### ML Training Integration
- **Supported Frameworks**: Scikit-learn, PyTorch, TensorFlow
- **Automated Pipelines**: End-to-end training workflows
- **Resource Management**: Compute resource allocation
- **Model Versioning**: Track training iterations
- **Performance Metrics**: Comprehensive evaluation

### Token Economics
- **Staking Rewards**: 5% annual rewards for staked NCR
- **Transaction Fees**: 0.25% fee on marketplace transactions
- **Governance Rights**: Token-weighted voting
- **Deflationary Mechanism**: Token burning on disputes
- **Liquidity Mining**: Rewards for providing liquidity

## 📈 Analytics & Monitoring

### User Analytics
- **Dashboard Metrics**: Real-time user statistics
- **Transaction History**: Complete audit trail
- **Performance Tracking**: Dataset popularity and earnings
- **Reputation System**: Quality-based scoring

### System Monitoring
- **Health Checks**: Automated system status monitoring
- **Performance Metrics**: Response times and throughput
- **Error Tracking**: Comprehensive error logging
- **Resource Usage**: CPU, memory, and storage monitoring

## 🧪 Testing

### Backend Testing

```bash
# Unit tests
python manage.py test apps.authentication
python manage.py test apps.datasets
python manage.py test apps.marketplace

# Integration tests
python manage.py test tests.test_integration

# Coverage report
coverage run --source='.' manage.py test
coverage html
```

### Frontend Testing

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Component tests
npm run test:components
```

### Smart Contract Testing

```bash
# Contract tests
npx hardhat test

# Gas optimization
npx hardhat test --gas-reporter

# Security analysis
npm run security-check
```

## 🚀 Deployment

### Production Environment

#### Backend Deployment

```bash
# Environment setup
export DJANGO_SETTINGS_MODULE=neurodata.settings.production
export DEBUG=False

# Database migration
python manage.py migrate --no-input

# Static files
python manage.py collectstatic --no-input

# Start services
gunicorn neurodata.wsgi:application
celery -A neurodata worker -D
celery -A neurodata beat -D
```

#### Frontend Deployment

```bash
# Build for production
npm run build

# Deploy to CDN/Static hosting
# Files in build/ directory
```

#### Smart Contract Deployment

```bash
# Deploy to mainnet
npx hardhat run scripts/deploy.js --network polygon

# Verify contracts
npx hardhat verify --network polygon CONTRACT_ADDRESS
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale web=3

# Monitor logs
docker-compose logs -f
```

### Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f infrastructure/kubernetes/

# Check status
kubectl get pods -n neurodata

# Scale deployment
kubectl scale deployment backend --replicas=3
```

## 🔍 Troubleshooting

### Common Issues

#### Backend Issues

**Database Connection Error**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Reset database
python manage.py flush
python manage.py migrate
```

**Redis Connection Error**
```bash
# Check Redis status
redis-cli ping

# Clear Redis cache
redis-cli flushall
```

#### Frontend Issues

**MetaMask Connection Issues**
```javascript
// Check MetaMask installation
if (typeof window.ethereum === 'undefined') {
  console.error('MetaMask not installed');
}

// Network configuration
await window.ethereum.request({
  method: 'wallet_switchEthereumChain',
  params: [{ chainId: '0x13881' }], // Mumbai testnet
});
```

#### Smart Contract Issues

**Gas Estimation Errors**
```bash
# Increase gas limit
npx hardhat run scripts/deploy.js --network mumbai --gas-limit 8000000

# Check gas price
npx hardhat run scripts/check-gas.js
```

### Debug Mode

```bash
# Backend debug
DEBUG=True python manage.py runserver

# Frontend debug
REACT_APP_DEBUG=true npm start

# Contract debug
npx hardhat node --verbose
```

## 📚 Additional Resources(documentation Incomplete)

### Documentation
- [API Documentation](./API_DOCUMENTATION.md)
- [Smart Contract Documentation](../contracts/README.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Security Audit](./SECURITY_AUDIT.md)

### Community(will be published when the platform is up)




## 🤝 Contributing

We welcome contributions! will love your idea and contribution, will allow you to contribute once the platform meet certain state .

### Development Setup(code is private but will be published once the platform is up and running)

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Standards

- **Python**: Follow PEP 8, use Black for formatting
- **TypeScript**: Follow ESLint rules, use Prettier
- **Solidity**: Follow Solidity style guide
- **Git**: Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenZeppelin**: Smart contract security frameworks
- **Django Community**: Excellent web framework and ecosystem
- **React Team**: Modern frontend development tools
- **Ethereum Foundation**: Blockchain infrastructure
- **IPFS**: Decentralized storage protocol

---

**Built by Sameer Gul NeuroData**


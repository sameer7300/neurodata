# NeuroData Smart Contracts

This repository contains the smart contracts for the NeuroData decentralized data marketplace platform.

## 🏗️ Architecture Overview

The NeuroData ecosystem consists of four main smart contracts:

### 1. NeuroCoin (NRC) - ERC-20 Token
- **Purpose**: Native utility token for the NeuroData ecosystem
- **Features**:
  - Standard ERC-20 functionality with 18 decimals
  - Staking mechanism with rewards
  - Transaction fee system
  - Marketplace integration
  - Pausable transfers for emergency situations
  - Burnable tokens
  - Owner-controlled minting (up to max supply)

### 2. DatasetMarketplace
- **Purpose**: Core marketplace for dataset trading
- **Features**:
  - Dataset listing and management
  - Secure purchase workflow with escrow
  - Bulk purchase discounts
  - Review and rating system
  - Dispute resolution mechanism
  - Revenue sharing between platform and sellers

### 3. EscrowManager
- **Purpose**: Advanced escrow system for secure transactions
- **Features**:
  - Multi-party escrow support
  - Milestone-based releases
  - Community-based dispute resolution
  - Automated escrow release
  - Emergency recovery mechanisms

### 4. TransactionLogger
- **Purpose**: Comprehensive transaction logging and analytics
- **Features**:
  - Detailed transaction recording
  - User activity analytics
  - Platform statistics
  - Revenue tracking
  - Gas-optimized batch operations

## 🚀 Quick Start

### Prerequisites

- Node.js >= 16.0.0
- npm >= 8.0.0
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/neurodata/smart-contracts.git
cd smart-contracts

# Install dependencies
npm install

# Create environment file
cp .env.example .env
# Edit .env with your configuration
```

### Environment Variables

Create a `.env` file with the following variables:

```env
# Private key for deployment (without 0x prefix)
PRIVATE_KEY=your_private_key_here

# API Keys
INFURA_API_KEY=your_infura_key
ALCHEMY_API_KEY=your_alchemy_key
ETHERSCAN_API_KEY=your_etherscan_key
POLYGONSCAN_API_KEY=your_polygonscan_key
BSCSCAN_API_KEY=your_bscscan_key

# Optional: Gas reporting
REPORT_GAS=true
COINMARKETCAP_API_KEY=your_cmc_key

# Optional: Monitoring
TENDERLY_PROJECT=your_project
TENDERLY_USERNAME=your_username
DEFENDER_API_KEY=your_defender_key
DEFENDER_API_SECRET=your_defender_secret
```

## 🔧 Development

### Compile Contracts

```bash
npm run compile
```

### Run Tests

```bash
# Run all tests
npm test

# Run tests with gas reporting
npm run test:gas

# Run coverage analysis
npm run test:coverage
```

### Deploy Contracts

```bash
# Deploy to local hardhat network
npm run node  # In one terminal
npm run deploy:local  # In another terminal

# Deploy to testnets
npm run deploy:sepolia
npm run deploy:mumbai
npm run deploy:bsc-testnet

# Deploy to mainnets (use with caution!)
npm run deploy:mainnet
npm run deploy:polygon
npm run deploy:bsc
```

### Verify Contracts

```bash
# Verify on Etherscan
npm run verify:sepolia
npm run verify:mainnet

# Verify on Polygonscan
npm run verify:mumbai
```

## 📋 Contract Specifications

### NeuroCoin (NRC)

| Parameter | Value |
|-----------|-------|
| Name | NeuroCoin |
| Symbol | NRC |
| Decimals | 18 |
| Initial Supply | 100,000,000 NRC |
| Max Supply | 1,000,000,000 NRC |
| Transaction Fee | 0.25% (configurable) |
| Staking Period | 30 days |
| Staking Reward | 5% annual |

### DatasetMarketplace

| Parameter | Value |
|-----------|-------|
| Platform Fee | 2.5% (configurable) |
| Escrow Period | 7 days |
| Dispute Period | 14 days |
| Bulk Discounts | 5% (5+ items), 10% (10+ items), 15% (25+ items) |

### EscrowManager

| Parameter | Value |
|-----------|-------|
| Default Escrow Period | 7 days |
| Max Escrow Period | 90 days |
| Dispute Window | 14 days |
| Arbitration Fee | 10% of disputed amount |

## 🧪 Testing

The test suite includes comprehensive tests for all contracts:

- **Unit Tests**: Test individual contract functions
- **Integration Tests**: Test contract interactions
- **Gas Optimization Tests**: Ensure efficient gas usage
- **Security Tests**: Test for common vulnerabilities

### Test Coverage

Run coverage analysis to ensure comprehensive testing:

```bash
npm run test:coverage
```

Target coverage: >95% for all contracts.

## 🔐 Security

### Security Measures

1. **Access Control**: Role-based permissions using OpenZeppelin's Ownable
2. **Reentrancy Protection**: ReentrancyGuard on all state-changing functions
3. **Pausable Contracts**: Emergency pause functionality
4. **Input Validation**: Comprehensive parameter validation
5. **Integer Overflow Protection**: Using Solidity 0.8.x built-in checks
6. **Rate Limiting**: Protection against spam and abuse

### Audit Checklist

- [ ] Static analysis with Slither
- [ ] Mythril security analysis
- [ ] Manual code review
- [ ] Testnet deployment and testing
- [ ] Third-party security audit
- [ ] Bug bounty program

### Security Tools

```bash
# Static analysis
npm run analyze

# Mythril analysis
npm run mythril

# Linting
npm run lint
npm run lint:fix
```

## 📊 Gas Optimization

### Gas Usage Estimates

| Contract | Deployment Gas | Average Function Gas |
|----------|----------------|---------------------|
| NeuroCoin | ~2,500,000 | 50,000 - 150,000 |
| DatasetMarketplace | ~3,500,000 | 80,000 - 200,000 |
| EscrowManager | ~3,000,000 | 70,000 - 180,000 |
| TransactionLogger | ~2,000,000 | 40,000 - 100,000 |

### Optimization Techniques

1. **Batch Operations**: Reduce multiple transactions to single calls
2. **Storage Optimization**: Efficient data structure packing
3. **Event Logging**: Use events instead of storage for historical data
4. **View Functions**: Minimize state reads in view functions
5. **Assembly Usage**: Critical path optimizations where necessary

## 🌐 Network Deployment

### Supported Networks

| Network | Chain ID | Status | Contract Addresses |
|---------|----------|--------|--------------------|
| Ethereum Mainnet | 1 | ✅ Supported | [View Addresses](./deployments/mainnet.json) |
| Polygon | 137 | ✅ Supported | [View Addresses](./deployments/polygon.json) |
| BSC | 56 | ✅ Supported | [View Addresses](./deployments/bsc.json) |
| Arbitrum | 42161 | 🔄 Planned | - |
| Optimism | 10 | 🔄 Planned | - |

### Testnet Addresses

| Network | Chain ID | Contract Addresses |
|---------|----------|--------------------|
| Sepolia | 11155111 | [View Addresses](./deployments/sepolia.json) |
| Mumbai | 80001 | [View Addresses](./deployments/mumbai.json) |
| BSC Testnet | 97 | [View Addresses](./deployments/bsc-testnet.json) |

## 🔄 Upgrade Strategy

### Upgradeability

Currently, the contracts are **non-upgradeable** for security and decentralization. Future versions may implement:

1. **Proxy Patterns**: For critical bug fixes
2. **Migration Contracts**: For major feature additions
3. **Governance**: Community-controlled upgrades

### Migration Process

1. Deploy new contract versions
2. Pause old contracts
3. Migrate critical state
4. Update frontend integrations
5. Communicate changes to users

## 📚 Integration Guide

### Frontend Integration

```javascript
// Example: Connect to NeuroCoin contract
import { ethers } from 'ethers';
import NeuroCoinABI from './abis/NeuroCoin.json';

const provider = new ethers.providers.Web3Provider(window.ethereum);
const signer = provider.getSigner();
const neuroCoin = new ethers.Contract(
  'CONTRACT_ADDRESS',
  NeuroCoinABI,
  signer
);

// Get user balance
const balance = await neuroCoin.balanceOf(userAddress);

// Transfer tokens
const tx = await neuroCoin.transfer(recipientAddress, amount);
await tx.wait();
```

### Backend Integration

```javascript
// Example: Monitor marketplace events
const marketplace = new ethers.Contract(
  'MARKETPLACE_ADDRESS',
  MarketplaceABI,
  provider
);

// Listen for dataset purchases
marketplace.on('DatasetPurchased', (purchaseId, datasetId, buyer, seller, amount) => {
  console.log(`New purchase: ${purchaseId}`);
  // Handle purchase logic
});
```

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Implement the feature
5. Run tests and ensure coverage
6. Submit a pull request

### Code Standards

- Follow Solidity style guide
- Use NatSpec documentation
- Maintain >95% test coverage
- Pass all security checks
- Optimize for gas efficiency

### Pull Request Process

1. Update documentation
2. Add/update tests
3. Run full test suite
4. Update CHANGELOG.md
5. Request review from maintainers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation

- [API Documentation](./docs/api.md)
- [Integration Guide](./docs/integration.md)
- [Security Best Practices](./docs/security.md)

### Community

- [Discord](https://discord.gg/neurodata)
- [Telegram](https://t.me/neurodata)
- [Twitter](https://twitter.com/neurodataio)

### Issues

For bug reports and feature requests, please use [GitHub Issues](https://github.com/neurodata/smart-contracts/issues).

## 🗺️ Roadmap

### Phase 1 (Current)
- [x] Core contract development
- [x] Comprehensive testing
- [x] Security audits
- [x] Testnet deployment

### Phase 2 (Q2 2024)
- [ ] Mainnet deployment
- [ ] Frontend integration
- [ ] Community testing
- [ ] Bug bounty program

### Phase 3 (Q3 2024)
- [ ] Advanced features
- [ ] Cross-chain support
- [ ] Governance implementation
- [ ] DAO transition

### Phase 4 (Q4 2024)
- [ ] Layer 2 scaling
- [ ] Advanced analytics
- [ ] Enterprise features
- [ ] Global expansion

---

**⚠️ Disclaimer**: These smart contracts are provided as-is. Users should conduct their own security audits and due diligence before using in production. The NeuroData team is not responsible for any losses incurred through the use of these contracts.

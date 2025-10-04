const { ethers, upgrades } = require("hardhat");
const fs = require("fs");
const path = require("path");

// Deployment configuration
const DEPLOYMENT_CONFIG = {
  // Token configuration
  INITIAL_SUPPLY: ethers.utils.parseEther("100000000"), // 100M NRC
  MAX_SUPPLY: ethers.utils.parseEther("1000000000"), // 1B NRC
  
  // Platform configuration
  PLATFORM_FEE_RATE: 250, // 2.5%
  ESCROW_PERIOD: 7 * 24 * 60 * 60, // 7 days
  DISPUTE_PERIOD: 14 * 24 * 60 * 60, // 14 days
  
  // Network configurations
  networks: {
    mainnet: {
      chainId: 1,
      gasPrice: ethers.utils.parseUnits("20", "gwei"),
      gasLimit: 8000000
    },
    polygon: {
      chainId: 137,
      gasPrice: ethers.utils.parseUnits("30", "gwei"),
      gasLimit: 8000000
    },
    bsc: {
      chainId: 56,
      gasPrice: ethers.utils.parseUnits("5", "gwei"),
      gasLimit: 8000000
    },
    sepolia: {
      chainId: 11155111,
      gasPrice: ethers.utils.parseUnits("10", "gwei"),
      gasLimit: 8000000
    }
  }
};

// Deployment addresses storage
let deploymentAddresses = {};

async function main() {
  console.log("🚀 Starting NeuroData Smart Contract Deployment...\n");
  
  // Get network info
  const network = await ethers.provider.getNetwork();
  console.log(`📡 Deploying to network: ${network.name} (Chain ID: ${network.chainId})`);
  
  // Get deployer account
  const [deployer] = await ethers.getSigners();
  console.log(`👤 Deployer address: ${deployer.address}`);
  
  const balance = await deployer.getBalance();
  console.log(`💰 Deployer balance: ${ethers.utils.formatEther(balance)} ETH\n`);
  
  try {
    // Step 1: Deploy NeuroCoin Token
    console.log("📝 Step 1: Deploying NeuroCoin (NRC) Token...");
    const neuroCoin = await deployNeuroCoin(deployer);
    
    // Step 2: Deploy Transaction Logger
    console.log("📝 Step 2: Deploying Transaction Logger...");
    const transactionLogger = await deployTransactionLogger();
    
    // Step 3: Deploy Escrow Manager
    console.log("📝 Step 3: Deploying Escrow Manager...");
    const escrowManager = await deployEscrowManager(neuroCoin.address, deployer.address);
    
    // Step 4: Deploy Dataset Marketplace
    console.log("📝 Step 4: Deploying Dataset Marketplace...");
    const marketplace = await deployDatasetMarketplace(neuroCoin.address, deployer.address);
    
    // Step 5: Configure contracts
    console.log("📝 Step 5: Configuring contracts...");
    await configureContracts(neuroCoin, marketplace, escrowManager, transactionLogger);
    
    // Step 6: Verify contracts (if on public network)
    if (network.chainId !== 31337) { // Not local hardhat network
      console.log("📝 Step 6: Verifying contracts...");
      await verifyContracts();
    }
    
    // Step 7: Save deployment info
    console.log("📝 Step 7: Saving deployment information...");
    await saveDeploymentInfo(network);
    
    console.log("\n✅ Deployment completed successfully!");
    console.log("📋 Deployment Summary:");
    console.log(`   NeuroCoin: ${deploymentAddresses.neuroCoin}`);
    console.log(`   Marketplace: ${deploymentAddresses.marketplace}`);
    console.log(`   Escrow Manager: ${deploymentAddresses.escrowManager}`);
    console.log(`   Transaction Logger: ${deploymentAddresses.transactionLogger}`);
    
  } catch (error) {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  }
}

async function deployNeuroCoin(deployer) {
  const NeuroCoin = await ethers.getContractFactory("NeuroCoin");
  
  console.log("   Deploying NeuroCoin contract...");
  const neuroCoin = await NeuroCoin.deploy(deployer.address);
  await neuroCoin.deployed();
  
  deploymentAddresses.neuroCoin = neuroCoin.address;
  console.log(`   ✅ NeuroCoin deployed to: ${neuroCoin.address}`);
  
  // Verify initial state
  const name = await neuroCoin.name();
  const symbol = await neuroCoin.symbol();
  const totalSupply = await neuroCoin.totalSupply();
  
  console.log(`   📊 Token Info: ${name} (${symbol})`);
  console.log(`   📊 Initial Supply: ${ethers.utils.formatEther(totalSupply)} NRC\n`);
  
  return neuroCoin;
}

async function deployTransactionLogger() {
  const TransactionLogger = await ethers.getContractFactory("TransactionLogger");
  
  console.log("   Deploying Transaction Logger contract...");
  const transactionLogger = await TransactionLogger.deploy();
  await transactionLogger.deployed();
  
  deploymentAddresses.transactionLogger = transactionLogger.address;
  console.log(`   ✅ Transaction Logger deployed to: ${transactionLogger.address}\n`);
  
  return transactionLogger;
}

async function deployEscrowManager(neuroCoinAddress, arbitrator) {
  const EscrowManager = await ethers.getContractFactory("EscrowManager");
  
  console.log("   Deploying Escrow Manager contract...");
  const escrowManager = await EscrowManager.deploy(neuroCoinAddress, arbitrator);
  await escrowManager.deployed();
  
  deploymentAddresses.escrowManager = escrowManager.address;
  console.log(`   ✅ Escrow Manager deployed to: ${escrowManager.address}\n`);
  
  return escrowManager;
}

async function deployDatasetMarketplace(neuroCoinAddress, feeRecipient) {
  const DatasetMarketplace = await ethers.getContractFactory("DatasetMarketplace");
  
  console.log("   Deploying Dataset Marketplace contract...");
  const marketplace = await DatasetMarketplace.deploy(neuroCoinAddress, feeRecipient);
  await marketplace.deployed();
  
  deploymentAddresses.marketplace = marketplace.address;
  console.log(`   ✅ Dataset Marketplace deployed to: ${marketplace.address}\n`);
  
  return marketplace;
}

async function configureContracts(neuroCoin, marketplace, escrowManager, transactionLogger) {
  console.log("   Configuring contract permissions...");
  
  // Authorize marketplace in NeuroCoin
  await neuroCoin.setMarketplaceAuthorization(marketplace.address, true);
  console.log("   ✅ Marketplace authorized in NeuroCoin");
  
  // Authorize contracts in Transaction Logger
  await transactionLogger.setAuthorizedLogger(marketplace.address, true);
  await transactionLogger.setAuthorizedLogger(escrowManager.address, true);
  console.log("   ✅ Contracts authorized in Transaction Logger");
  
  // Set bulk discounts in marketplace
  await marketplace.setBulkDiscount(5, 500);   // 5% for 5+ items
  await marketplace.setBulkDiscount(10, 1000); // 10% for 10+ items
  await marketplace.setBulkDiscount(25, 1500); // 15% for 25+ items
  console.log("   ✅ Bulk discounts configured");
  
  console.log("   ✅ Contract configuration completed\n");
}

async function verifyContracts() {
  console.log("   Starting contract verification...");
  
  try {
    // Verify NeuroCoin
    await hre.run("verify:verify", {
      address: deploymentAddresses.neuroCoin,
      constructorArguments: [deploymentAddresses.deployer],
    });
    console.log("   ✅ NeuroCoin verified");
    
    // Verify Transaction Logger
    await hre.run("verify:verify", {
      address: deploymentAddresses.transactionLogger,
      constructorArguments: [],
    });
    console.log("   ✅ Transaction Logger verified");
    
    // Verify Escrow Manager
    await hre.run("verify:verify", {
      address: deploymentAddresses.escrowManager,
      constructorArguments: [deploymentAddresses.neuroCoin, deploymentAddresses.deployer],
    });
    console.log("   ✅ Escrow Manager verified");
    
    // Verify Dataset Marketplace
    await hre.run("verify:verify", {
      address: deploymentAddresses.marketplace,
      constructorArguments: [deploymentAddresses.neuroCoin, deploymentAddresses.deployer],
    });
    console.log("   ✅ Dataset Marketplace verified");
    
  } catch (error) {
    console.log("   ⚠️  Contract verification failed (this is normal for testnets)");
    console.log(`   Error: ${error.message}`);
  }
  
  console.log("");
}

async function saveDeploymentInfo(network) {
  const deploymentInfo = {
    network: {
      name: network.name,
      chainId: network.chainId,
      timestamp: new Date().toISOString()
    },
    contracts: deploymentAddresses,
    configuration: DEPLOYMENT_CONFIG,
    gasUsed: {
      // This would be populated during actual deployment
      neuroCoin: "TBD",
      marketplace: "TBD",
      escrowManager: "TBD",
      transactionLogger: "TBD"
    }
  };
  
  // Save to JSON file
  const deploymentDir = path.join(__dirname, "../deployments");
  if (!fs.existsSync(deploymentDir)) {
    fs.mkdirSync(deploymentDir, { recursive: true });
  }
  
  const filename = `deployment-${network.name}-${Date.now()}.json`;
  const filepath = path.join(deploymentDir, filename);
  
  fs.writeFileSync(filepath, JSON.stringify(deploymentInfo, null, 2));
  console.log(`   ✅ Deployment info saved to: ${filepath}`);
  
  // Also save latest deployment
  const latestPath = path.join(deploymentDir, `latest-${network.name}.json`);
  fs.writeFileSync(latestPath, JSON.stringify(deploymentInfo, null, 2));
  console.log(`   ✅ Latest deployment info saved to: ${latestPath}`);
  
  // Generate ABI files for frontend
  await generateABIFiles();
}

async function generateABIFiles() {
  console.log("   Generating ABI files for frontend...");
  
  const contracts = [
    "NeuroCoin",
    "DatasetMarketplace", 
    "EscrowManager",
    "TransactionLogger"
  ];
  
  const abiDir = path.join(__dirname, "../abis");
  if (!fs.existsSync(abiDir)) {
    fs.mkdirSync(abiDir, { recursive: true });
  }
  
  for (const contractName of contracts) {
    try {
      const Contract = await ethers.getContractFactory(contractName);
      const abi = Contract.interface.format(ethers.utils.FormatTypes.json);
      
      const abiPath = path.join(abiDir, `${contractName}.json`);
      fs.writeFileSync(abiPath, abi);
      console.log(`   ✅ ${contractName} ABI saved`);
    } catch (error) {
      console.log(`   ⚠️  Failed to generate ABI for ${contractName}: ${error.message}`);
    }
  }
  
  // Generate combined contract info for frontend
  const contractInfo = {
    addresses: deploymentAddresses,
    abis: {}
  };
  
  for (const contractName of contracts) {
    try {
      const abiPath = path.join(abiDir, `${contractName}.json`);
      if (fs.existsSync(abiPath)) {
        contractInfo.abis[contractName] = JSON.parse(fs.readFileSync(abiPath, 'utf8'));
      }
    } catch (error) {
      console.log(`   ⚠️  Failed to read ABI for ${contractName}`);
    }
  }
  
  const contractInfoPath = path.join(abiDir, 'contracts.json');
  fs.writeFileSync(contractInfoPath, JSON.stringify(contractInfo, null, 2));
  console.log(`   ✅ Combined contract info saved to: ${contractInfoPath}`);
}

// Utility functions
async function estimateGasCosts() {
  console.log("📊 Estimating deployment gas costs...");
  
  const gasPrice = await ethers.provider.getGasPrice();
  console.log(`   Current gas price: ${ethers.utils.formatUnits(gasPrice, "gwei")} gwei`);
  
  // Estimated gas costs (these would be actual estimates in real deployment)
  const estimates = {
    neuroCoin: 2500000,
    marketplace: 3500000,
    escrowManager: 3000000,
    transactionLogger: 2000000
  };
  
  let totalGas = 0;
  for (const [contract, gas] of Object.entries(estimates)) {
    const cost = gasPrice.mul(gas);
    totalGas += gas;
    console.log(`   ${contract}: ${gas.toLocaleString()} gas (~${ethers.utils.formatEther(cost)} ETH)`);
  }
  
  const totalCost = gasPrice.mul(totalGas);
  console.log(`   Total estimated cost: ${totalGas.toLocaleString()} gas (~${ethers.utils.formatEther(totalCost)} ETH)\n`);
}

// Error handling
process.on('unhandledRejection', (error) => {
  console.error('❌ Unhandled promise rejection:', error);
  process.exit(1);
});

// Run deployment
if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

module.exports = {
  main,
  deployNeuroCoin,
  deployDatasetMarketplace,
  deployEscrowManager,
  deployTransactionLogger,
  DEPLOYMENT_CONFIG
};

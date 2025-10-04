require("@nomicfoundation/hardhat-toolbox");
require("@openzeppelin/hardhat-upgrades");
require("hardhat-gas-reporter");
require("solidity-coverage");
require("hardhat-contract-sizer");
require("dotenv").config();

// Network configuration
const PRIVATE_KEY = process.env.PRIVATE_KEY || "0x" + "0".repeat(64);
const INFURA_API_KEY = process.env.INFURA_API_KEY || "";
const ALCHEMY_API_KEY = process.env.ALCHEMY_API_KEY || "";
const ETHERSCAN_API_KEY = process.env.ETHERSCAN_API_KEY || "";
const POLYGONSCAN_API_KEY = process.env.POLYGONSCAN_API_KEY || "";
const BSCSCAN_API_KEY = process.env.BSCSCAN_API_KEY || "";

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      viaIR: true, // Enable intermediate representation for better optimization
    },
  },
  
  networks: {
    // Local development
    hardhat: {
      chainId: 31337,
      gas: 12000000,
      blockGasLimit: 12000000,
      allowUnlimitedContractSize: true,
      accounts: {
        count: 20,
        accountsBalance: "10000000000000000000000", // 10,000 ETH
      },
    },
    
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
    },
    
    // Ethereum Mainnet
    mainnet: {
      url: `https://mainnet.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 1,
      gasPrice: 20000000000, // 20 gwei
      gas: 8000000,
    },
    
    // Ethereum Testnets
    sepolia: {
      url: `https://sepolia.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 11155111,
      gasPrice: 10000000000, // 10 gwei
      gas: 8000000,
    },
    
    goerli: {
      url: `https://goerli.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 5,
      gasPrice: 10000000000, // 10 gwei
      gas: 8000000,
    },
    
    // Polygon
    polygon: {
      url: `https://polygon-mainnet.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 137,
      gasPrice: 30000000000, // 30 gwei
      gas: 8000000,
    },
    
    mumbai: {
      url: `https://polygon-mumbai.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 80001,
      gasPrice: 10000000000, // 10 gwei
      gas: 8000000,
    },
    
    // Binance Smart Chain
    bsc: {
      url: "https://bsc-dataseed1.binance.org/",
      accounts: [PRIVATE_KEY],
      chainId: 56,
      gasPrice: 5000000000, // 5 gwei
      gas: 8000000,
    },
    
    bscTestnet: {
      url: "https://data-seed-prebsc-1-s1.binance.org:8545/",
      accounts: [PRIVATE_KEY],
      chainId: 97,
      gasPrice: 10000000000, // 10 gwei
      gas: 8000000,
    },
    
    // Arbitrum
    arbitrum: {
      url: "https://arb1.arbitrum.io/rpc",
      accounts: [PRIVATE_KEY],
      chainId: 42161,
      gasPrice: 1000000000, // 1 gwei
      gas: 8000000,
    },
    
    arbitrumGoerli: {
      url: "https://goerli-rollup.arbitrum.io/rpc",
      accounts: [PRIVATE_KEY],
      chainId: 421613,
      gasPrice: 1000000000, // 1 gwei
      gas: 8000000,
    },
    
    // Optimism
    optimism: {
      url: "https://mainnet.optimism.io",
      accounts: [PRIVATE_KEY],
      chainId: 10,
      gasPrice: 1000000000, // 1 gwei
      gas: 8000000,
    },
    
    optimismGoerli: {
      url: "https://goerli.optimism.io",
      accounts: [PRIVATE_KEY],
      chainId: 420,
      gasPrice: 1000000000, // 1 gwei
      gas: 8000000,
    },
  },
  
  // Contract verification
  etherscan: {
    apiKey: {
      mainnet: ETHERSCAN_API_KEY,
      sepolia: ETHERSCAN_API_KEY,
      goerli: ETHERSCAN_API_KEY,
      polygon: POLYGONSCAN_API_KEY,
      polygonMumbai: POLYGONSCAN_API_KEY,
      bsc: BSCSCAN_API_KEY,
      bscTestnet: BSCSCAN_API_KEY,
    },
  },
  
  // Gas reporting
  gasReporter: {
    enabled: process.env.REPORT_GAS !== undefined,
    currency: "USD",
    gasPrice: 20, // gwei
    coinmarketcap: process.env.COINMARKETCAP_API_KEY,
    excludeContracts: ["Migrations"],
    src: "./contracts",
    showTimeSpent: true,
    showMethodSig: true,
    maxMethodDiff: 10,
  },
  
  // Contract size reporting
  contractSizer: {
    alphaSort: true,
    disambiguatePaths: false,
    runOnCompile: true,
    strict: true,
    only: [
      "NeuroCoin",
      "DatasetMarketplace",
      "EscrowManager",
      "TransactionLogger",
    ],
  },
  
  // Test configuration
  mocha: {
    timeout: 60000, // 60 seconds
    reporter: "spec",
    slow: 2000,
  },
  
  // Paths
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
    deploy: "./deploy",
  },
  
  // Compiler settings
  typechain: {
    outDir: "typechain-types",
    target: "ethers-v5",
    alwaysGenerateOverloads: false,
    externalArtifacts: ["externalArtifacts/*.json"],
  },
  
  // Coverage settings
  solidity_coverage: {
    skipFiles: [
      "test/",
      "mock/",
      "interfaces/",
    ],
  },
  
  // Custom tasks
  tasks: {
    deploy: {
      description: "Deploy all contracts",
      action: require("./deploy/deploy.js").main,
    },
  },
  
  // Warnings configuration
  warnings: {
    "*": {
      "code-size": "error",
      "unused-param": "warn",
      "unused-var": "warn",
      "unreachable-code": "error",
    },
  },
  
  // External contracts (for testing and integration)
  external: {
    contracts: [
      {
        artifacts: "node_modules/@openzeppelin/contracts/build/contracts",
      },
    ],
  },
  
  // Defender (for automated operations)
  defender: {
    apiKey: process.env.DEFENDER_API_KEY,
    apiSecret: process.env.DEFENDER_API_SECRET,
  },
  
  // Tenderly (for debugging and monitoring)
  tenderly: {
    project: process.env.TENDERLY_PROJECT,
    username: process.env.TENDERLY_USERNAME,
  },
};

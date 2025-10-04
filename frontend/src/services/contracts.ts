import { ethers, BrowserProvider, Contract, formatEther, parseEther } from 'ethers';

// Contract addresses (these should be from your deployment)
export const CONTRACTS = {
  DATASET_MARKETPLACE: process.env.REACT_APP_MARKETPLACE_CONTRACT || '0x0000000000000000000000000000000000000000',
  NEURO_COIN: process.env.REACT_APP_NEUROCOIN_CONTRACT || '0x0000000000000000000000000000000000000000',
};

// Contract ABIs (simplified for the purchase function)
export const MARKETPLACE_ABI = [
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "datasetId",
        "type": "uint256"
      }
    ],
    "name": "purchaseDataset",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "datasetId",
        "type": "uint256"
      }
    ],
    "name": "getDataset",
    "outputs": [
      {
        "components": [
          {
            "internalType": "uint256",
            "name": "id",
            "type": "uint256"
          },
          {
            "internalType": "address",
            "name": "seller",
            "type": "address"
          },
          {
            "internalType": "string",
            "name": "ipfsHash",
            "type": "string"
          },
          {
            "internalType": "string",
            "name": "metadataHash",
            "type": "string"
          },
          {
            "internalType": "uint256",
            "name": "price",
            "type": "uint256"
          },
          {
            "internalType": "string",
            "name": "title",
            "type": "string"
          },
          {
            "internalType": "string",
            "name": "description",
            "type": "string"
          },
          {
            "internalType": "string[]",
            "name": "tags",
            "type": "string[]"
          },
          {
            "internalType": "uint256",
            "name": "fileSize",
            "type": "uint256"
          },
          {
            "internalType": "string",
            "name": "fileType",
            "type": "string"
          }
        ],
        "internalType": "struct DatasetMarketplace.Dataset",
        "name": "",
        "type": "tuple"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
];

export const NEUROCOIN_ABI = [
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "spender",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "amount",
        "type": "uint256"
      }
    ],
    "name": "approve",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "owner",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "spender",
        "type": "address"
      }
    ],
    "name": "allowance",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "account",
        "type": "address"
      }
    ],
    "name": "balanceOf",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
];

// Contract service class
export class ContractService {
  private provider: BrowserProvider;
  private signer: ethers.Signer;
  private marketplaceContract: Contract;
  private neuroCoinContract: Contract;

  constructor(provider: BrowserProvider, signer: ethers.Signer) {
    this.provider = provider;
    this.signer = signer;
    this.marketplaceContract = new Contract(
      CONTRACTS.DATASET_MARKETPLACE,
      MARKETPLACE_ABI,
      signer
    );
    this.neuroCoinContract = new Contract(
      CONTRACTS.NEURO_COIN,
      NEUROCOIN_ABI,
      signer
    );
  }

  async purchaseDataset(datasetId: string, priceInEth: string): Promise<string> {
    try {
      // Convert price from ETH to Wei (assuming 1 NRC = 1 ETH for simplicity)
      const priceInWei = parseEther(priceInEth);
      
      // Check NRC balance
      const userAddress = await this.signer.getAddress();
      const balance = await this.neuroCoinContract.balanceOf(userAddress);
      
      if (balance.lt(priceInWei)) {
        throw new Error('Insufficient NRC balance');
      }

      // Check and approve NRC spending if necessary
      const allowance = await this.neuroCoinContract.allowance(
        userAddress,
        CONTRACTS.DATASET_MARKETPLACE
      );

      if (allowance.lt(priceInWei)) {
        console.log('Approving NRC spending...');
        const approveTx = await this.neuroCoinContract.approve(
          CONTRACTS.DATASET_MARKETPLACE,
          priceInWei
        );
        await approveTx.wait();
        console.log('NRC spending approved');
      }

      // Purchase the dataset
      console.log('Purchasing dataset...');
      const purchaseTx = await this.marketplaceContract.purchaseDataset(datasetId);
      const receipt = await purchaseTx.wait();
      
      console.log('Dataset purchased successfully:', receipt.transactionHash);
      return receipt.transactionHash;
    } catch (error: any) {
      console.error('Contract purchase error:', error);
      throw new Error(error.message || 'Smart contract transaction failed');
    }
  }

  async getDatasetInfo(datasetId: string) {
    try {
      const dataset = await this.marketplaceContract.getDataset(datasetId);
      return dataset;
    } catch (error) {
      console.error('Error fetching dataset from contract:', error);
      throw error;
    }
  }

  async getNRCBalance(address: string): Promise<string> {
    try {
      const balance = await this.neuroCoinContract.balanceOf(address);
      return formatEther(balance);
    } catch (error) {
      console.error('Error fetching NRC balance:', error);
      return '0';
    }
  }
}

export default ContractService;

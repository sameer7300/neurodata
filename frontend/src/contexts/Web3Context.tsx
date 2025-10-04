import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { ethers } from 'ethers';
import toast from 'react-hot-toast';

// Types
interface Web3ContextType {
  // Connection state
  isConnected: boolean;
  isConnecting: boolean;
  account: string | null;
  chainId: number | null;
  balance: string;
  
  // Provider and signer
  provider: ethers.BrowserProvider | null;
  signer: ethers.JsonRpcSigner | null;
  
  // Connection methods
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  switchNetwork: (chainId: number) => Promise<void>;
  
  // Contract interactions
  getContract: (address: string, abi: any[]) => ethers.Contract | null;
  
  // Network info
  networkName: string;
  isCorrectNetwork: boolean;
}

// Create context
const Web3Context = createContext<Web3ContextType | undefined>(undefined);

// Provider component
interface Web3ProviderProps {
  children: ReactNode;
}

export const Web3Provider: React.FC<Web3ProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [account, setAccount] = useState<string | null>(null);
  const [chainId, setChainId] = useState<number | null>(null);
  const [balance, setBalance] = useState('0');
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null);
  const [signer, setSigner] = useState<ethers.JsonRpcSigner | null>(null);

  // Network configuration
  const targetChainId = parseInt(process.env.REACT_APP_CHAIN_ID || '1337');
  const networkName = process.env.REACT_APP_NETWORK_NAME || 'localhost';

  // Check if MetaMask is installed
  const isMetaMaskInstalled = () => {
    return typeof window !== 'undefined' && typeof window.ethereum !== 'undefined';
  };

  // Connect wallet
  const connectWallet = useCallback(async () => {
    if (!isMetaMaskInstalled()) {
      toast.error('Please install MetaMask to connect your wallet');
      return;
    }

    setIsConnecting(true);
    try {
      // Request account access
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts',
      });

      if (accounts.length === 0) {
        throw new Error('No accounts found');
      }

      // Create provider and signer
      const web3Provider = new ethers.BrowserProvider(window.ethereum);
      const web3Signer = await web3Provider.getSigner();
      
      // Get network info
      const network = await web3Provider.getNetwork();
      const userBalance = await web3Provider.getBalance(accounts[0]);

      // Update state
      setProvider(web3Provider);
      setSigner(web3Signer);
      setAccount(accounts[0]);
      setChainId(Number(network.chainId));
      setBalance(ethers.formatEther(userBalance));
      setIsConnected(true);

      toast.success('Wallet connected successfully!');
    } catch (error: any) {
      console.error('Error connecting wallet:', error);
      toast.error(error.message || 'Failed to connect wallet');
    } finally {
      setIsConnecting(false);
    }
  }, []);

  // Disconnect wallet
  const disconnectWallet = () => {
    setProvider(null);
    setSigner(null);
    setAccount(null);
    setChainId(null);
    setBalance('0');
    setIsConnected(false);
    toast.success('Wallet disconnected');
  };

  // Switch network
  const switchNetwork = async (targetChainId: number) => {
    if (!window.ethereum) {
      toast.error('MetaMask not found');
      return;
    }

    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: `0x${targetChainId.toString(16)}` }],
      });
    } catch (error: any) {
      // If network doesn't exist, add it
      if (error.code === 4902) {
        try {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [
              {
                chainId: `0x${targetChainId.toString(16)}`,
                chainName: networkName,
                rpcUrls: [process.env.REACT_APP_RPC_URL || 'http://localhost:8545'],
                nativeCurrency: {
                  name: 'ETH',
                  symbol: 'ETH',
                  decimals: 18,
                },
              },
            ],
          });
        } catch (addError) {
          console.error('Error adding network:', addError);
          toast.error('Failed to add network');
        }
      } else {
        console.error('Error switching network:', error);
        toast.error('Failed to switch network');
      }
    }
  };

  // Get contract instance
  const getContract = (address: string, abi: any[]): ethers.Contract | null => {
    if (!signer) {
      console.error('No signer available');
      return null;
    }

    try {
      return new ethers.Contract(address, abi, signer);
    } catch (error) {
      console.error('Error creating contract instance:', error);
      return null;
    }
  };

  // Handle account changes
  useEffect(() => {
    if (!window.ethereum) return;

    const handleAccountsChanged = (accounts: string[]) => {
      if (accounts.length === 0) {
        disconnectWallet();
      } else if (accounts[0] !== account) {
        setAccount(accounts[0]);
        // Refresh balance
        if (provider) {
          provider.getBalance(accounts[0]).then((balance: bigint) => {
            setBalance(ethers.formatEther(balance));
          });
        }
      }
    };

    const handleChainChanged = (chainId: string) => {
      const newChainId = parseInt(chainId, 16);
      setChainId(newChainId);
      // Refresh the page to reset state
      window.location.reload();
    };

    window.ethereum.on('accountsChanged', handleAccountsChanged);
    window.ethereum.on('chainChanged', handleChainChanged);

    return () => {
      if (window.ethereum) {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
        window.ethereum.removeListener('chainChanged', handleChainChanged);
      }
    };
  }, [account, provider]);

  // Check if already connected on mount
  useEffect(() => {
    const checkConnection = async () => {
      if (!isMetaMaskInstalled()) return;

      try {
        const accounts = await window.ethereum.request({
          method: 'eth_accounts',
        });

        if (accounts.length > 0) {
          // Auto-connect if previously connected
          await connectWallet();
        }
      } catch (error) {
        console.error('Error checking connection:', error);
      }
    };

    checkConnection();
  }, [connectWallet]);

  const value: Web3ContextType = {
    isConnected,
    isConnecting,
    account,
    chainId,
    balance,
    provider,
    signer,
    connectWallet,
    disconnectWallet,
    switchNetwork,
    getContract,
    networkName,
    isCorrectNetwork: chainId === targetChainId,
  };

  return <Web3Context.Provider value={value}>{children}</Web3Context.Provider>;
};

// Hook to use Web3 context
export const useWeb3 = (): Web3ContextType => {
  const context = useContext(Web3Context);
  if (context === undefined) {
    throw new Error('useWeb3 must be used within a Web3Provider');
  }
  return context;
};

// Extend Window interface for TypeScript
declare global {
  interface Window {
    ethereum?: any;
  }
}

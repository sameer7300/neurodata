import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import toast from 'react-hot-toast';
import { useWeb3 } from './Web3Context';
import api from '../services/api';

// Types
interface User {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_verified: boolean;
  created_at: string;
  profile?: {
    wallet_address?: string;
    verification_status: string;
    reputation_score: number;
  };
}

interface AuthContextType {
  // Auth state
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Auth methods
  login: (email: string, password: string) => Promise<boolean>;
  register: (username: string, email: string, password: string) => Promise<boolean>;
  logout: () => void;
  
  // Wallet auth
  connectWalletAuth: () => Promise<boolean>;
  verifyWalletSignature: (signature: string, message: string) => Promise<boolean>;
  
  // Profile methods
  updateProfile: (data: Partial<User>) => Promise<boolean>;
  refreshUser: () => Promise<void>;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);


// Provider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  const { account, signer } = useWeb3();

  // Login with email/password
  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await api.post('/auth/login/', {
        email,
        password,
      });

      const { access, refresh, user: userData } = response.data;
      
      // Store tokens with expiry (30 minutes)
      const expiry = new Date().getTime() + (30 * 60 * 1000);
      localStorage.setItem('authToken', access);
      localStorage.setItem('refreshToken', refresh);
      localStorage.setItem('tokenExpiry', expiry.toString());
      
      // Update state
      setUser(userData);
      setIsAuthenticated(true);
      
      toast.success('Login successful!');
      return true;
    } catch (error: any) {
      console.error('Login error:', error);
      const message = error.response?.data?.message || 'Login failed';
      toast.error(message);
      return false;
    }
  };

  // Register new user
  const register = async (username: string, email: string, password: string): Promise<boolean> => {
    try {
      const response = await api.post('/auth/register/', {
        username,
        email,
        password,
      });

      const { user: userData, tokens } = response.data.data;
      const { access, refresh } = tokens;
      
      // Store tokens with expiry (30 minutes)
      const expiry = new Date().getTime() + (30 * 60 * 1000);
      localStorage.setItem('authToken', access);
      localStorage.setItem('refreshToken', refresh);
      localStorage.setItem('tokenExpiry', expiry.toString());
      
      // Update state
      setUser(userData);
      setIsAuthenticated(true);
      
      toast.success('Registration successful!');
      return true;
    } catch (error: any) {
      console.error('Registration error:', error);
      const message = error.response?.data?.message || 'Registration failed';
      toast.error(message);
      return false;
    }
  };

  // Logout
  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('tokenExpiry');
    setUser(null);
    setIsAuthenticated(false);
    toast.success('Logged out successfully!');
  };

  // Connect wallet authentication
  const connectWalletAuth = async (): Promise<boolean> => {
    if (!account || !signer) {
      toast.error('Please connect your wallet first');
      return false;
    }

    try {
      // Step 1: Get nonce from backend
      console.log('Step 1: Requesting nonce for wallet:', account);
      const nonceResponse = await api.post('/auth/wallet/connect/', {
        wallet_address: account,
      });

      console.log('Step 1 complete: Nonce response:', nonceResponse.data);
      const { nonce } = nonceResponse.data.data;

      // Step 2: Sign the message (nonce is the message to sign)
      console.log('Step 2: Requesting signature from MetaMask...');
      console.log('Message to sign:', nonce);
      
      // Add timeout for MetaMask signing
      const signaturePromise = signer.signMessage(nonce);
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('MetaMask signature timeout')), 60000);
      });
      
      const signature = await Promise.race([signaturePromise, timeoutPromise]);
      console.log('Step 2 complete: Signature obtained');

      // Step 3: Authenticate with signature
      console.log('Step 3: Authenticating with backend...');
      const authResponse = await api.post('/auth/wallet/auth/', {
        wallet_address: account,
        signature,
        nonce,
      });

      console.log('Step 3 complete: Auth response:', authResponse.data);

      if (authResponse.data.success) {
        const { user: userData, tokens } = authResponse.data.data;
        
        // Store tokens
        localStorage.setItem('authToken', tokens.access);
        localStorage.setItem('refreshToken', tokens.refresh);
        
        // Update state
        setUser(userData);
        setIsAuthenticated(true);
        
        toast.success('Wallet authentication successful!');
        return true;
      }

      return false;
    } catch (error: any) {
      console.error('Wallet auth error:', error);
      const message = error.response?.data?.message || 'Wallet authentication failed';
      toast.error(message);
      return false;
    }
  };

  // Verify wallet signature
  const verifyWalletSignature = async (signature: string, nonce: string): Promise<boolean> => {
    if (!account) {
      toast.error('No wallet connected');
      return false;
    }

    try {
      const response = await api.post('/auth/wallet/auth/', {
        wallet_address: account,
        signature,
        nonce,
      });

      return response.data.success;
    } catch (error: any) {
      console.error('Signature verification error:', error);
      return false;
    }
  };

  // Update user profile
  const updateProfile = async (data: Partial<User>): Promise<boolean> => {
    try {
      const response = await api.patch('/auth/profile/', data);
      
      if (response.data.success) {
        setUser(response.data.data);
        toast.success('Profile updated successfully!');
        return true;
      }
      
      return false;
    } catch (error: any) {
      console.error('Profile update error:', error);
      const message = error.response?.data?.message || 'Profile update failed';
      toast.error(message);
      return false;
    }
  };

  // Refresh user data
  const refreshUser = async (): Promise<void> => {
    try {
      const response = await api.get('/auth/user/');
      setUser(response.data);
    } catch (error) {
      console.error('Error refreshing user:', error);
    }
  };

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('authToken');
      const tokenExpiry = localStorage.getItem('tokenExpiry');
      
      // console.log('🔐 Auth check - Token exists:', !!token, 'Expiry stored:', !!tokenExpiry);
      
      if (token) {
        const now = new Date().getTime();
        
        // If no expiry time is stored (backward compatibility), treat as expired and try to refresh
        if (!tokenExpiry) {
          console.log('No expiry time found, treating as expired');
          const refreshToken = localStorage.getItem('refreshToken');
          if (refreshToken) {
            try {
              const response = await api.post('/auth/token/refresh/', {
                refresh: refreshToken
              });
              
              const { access } = response.data;
              const newExpiry = new Date().getTime() + (30 * 60 * 1000);
              
              localStorage.setItem('authToken', access);
              localStorage.setItem('tokenExpiry', newExpiry.toString());
              
              // Get user data
              const profileResponse = await api.get('/auth/user/');
              setUser(profileResponse.data);
              setIsAuthenticated(true);
            } catch (error) {
              console.error('Token refresh failed:', error);
              localStorage.removeItem('authToken');
              localStorage.removeItem('refreshToken');
              localStorage.removeItem('tokenExpiry');
            }
          } else {
            // No refresh token, just try to get user data with existing token
            try {
              const response = await api.get('/auth/user/');
              setUser(response.data);
              setIsAuthenticated(true);
              // Set expiry for future use
              const newExpiry = new Date().getTime() + (30 * 60 * 1000);
              localStorage.setItem('tokenExpiry', newExpiry.toString());
            } catch (error) {
              console.error('Profile fetch failed:', error);
              localStorage.removeItem('authToken');
              localStorage.removeItem('refreshToken');
              localStorage.removeItem('tokenExpiry');
            }
          }
        } else {
          const expiryTime = parseInt(tokenExpiry);
          console.log('Token expiry check - Now:', now, 'Expiry:', expiryTime, 'Expired:', now > expiryTime);
          
          // Check if token is expired
          if (now > expiryTime) {
            // Try to refresh token
            const refreshToken = localStorage.getItem('refreshToken');
            if (refreshToken) {
              try {
                const response = await api.post('/auth/token/refresh/', {
                  refresh: refreshToken
                });
                
                const { access } = response.data;
                const newExpiry = new Date().getTime() + (30 * 60 * 1000); // 30 minutes
                
                localStorage.setItem('authToken', access);
                localStorage.setItem('tokenExpiry', newExpiry.toString());
                
                // Get user data
                const profileResponse = await api.get('/auth/user/');
                setUser(profileResponse.data);
                setIsAuthenticated(true);
              } catch (error) {
                console.error('Token refresh failed:', error);
                // Refresh failed, clear tokens
                localStorage.removeItem('authToken');
                localStorage.removeItem('refreshToken');
                localStorage.removeItem('tokenExpiry');
              }
            } else {
              // No refresh token, clear everything
              localStorage.removeItem('authToken');
              localStorage.removeItem('refreshToken');
              localStorage.removeItem('tokenExpiry');
            }
          } else {
            // Token is still valid, get user profile
            try {
              console.log('🔄 Fetching user data...');
              const response = await api.get('/auth/user/');
              console.log('✅ User response:', response.data);
              setUser(response.data);
              setIsAuthenticated(true);
              console.log('✅ User authenticated successfully');
            } catch (error) {
              console.error('Profile fetch error:', error);
              // Token is invalid, clear it
              localStorage.removeItem('authToken');
              localStorage.removeItem('refreshToken');
              localStorage.removeItem('tokenExpiry');
            }
          }
        }
      }
      
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  // Auto-refresh token every 25 minutes to keep user logged in
  useEffect(() => {
    if (isAuthenticated) {
      const refreshInterval = setInterval(async () => {
        const refreshToken = localStorage.getItem('refreshToken');
        const tokenExpiry = localStorage.getItem('tokenExpiry');
        
        if (refreshToken && tokenExpiry) {
          const now = new Date().getTime();
          const expiryTime = parseInt(tokenExpiry);
          
          // Refresh token if it expires in the next 5 minutes
          if (now > (expiryTime - 5 * 60 * 1000)) {
            try {
              const response = await api.post('/auth/token/refresh/', {
                refresh: refreshToken
              });
              
              const { access } = response.data;
              const newExpiry = new Date().getTime() + (30 * 60 * 1000);
              
              localStorage.setItem('authToken', access);
              localStorage.setItem('tokenExpiry', newExpiry.toString());
            } catch (error) {
              // Refresh failed, logout user
              logout();
            }
          }
        }
      }, 5 * 60 * 1000); // Check every 5 minutes

      return () => clearInterval(refreshInterval);
    }
  }, [isAuthenticated]);

  // Auto-link wallet when connected
  useEffect(() => {
    const linkWallet = async () => {
      if (account && isAuthenticated && user && !user.profile?.wallet_address) {
        try {
          await api.post('/web3/wallet/link/', {
            wallet_address: account,
          });
          
          // Refresh user data
          await refreshUser();
          toast.success('Wallet linked to your account!');
        } catch (error) {
          console.error('Error linking wallet:', error);
        }
      }
    };

    linkWallet();
  }, [account, isAuthenticated, user]);

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    connectWalletAuth,
    verifyWalletSignature,
    updateProfile,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook to use Auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Export API instance for use in other components
export { api };

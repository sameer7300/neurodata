// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title NeuroCoin (NRC)
 * @dev ERC-20 token for the NeuroData decentralized data marketplace
 * 
 * Features:
 * - Standard ERC-20 functionality
 * - Burnable tokens
 * - Pausable transfers (for emergency situations)
 * - Owner-controlled minting
 * - Reentrancy protection
 * - Staking rewards mechanism
 * - Transaction fee redistribution
 */
contract NeuroCoin is ERC20, ERC20Burnable, ERC20Pausable, Ownable, ReentrancyGuard {
    
    // Token configuration
    uint8 private constant DECIMALS = 18;
    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10**DECIMALS; // 1 billion NRC
    uint256 public constant INITIAL_SUPPLY = 100_000_000 * 10**DECIMALS; // 100 million NRC
    
    // Fee configuration
    uint256 public transactionFeeRate = 25; // 0.25% (25/10000)
    uint256 public constant MAX_FEE_RATE = 500; // 5% maximum fee
    address public feeCollector;
    
    // Staking configuration
    mapping(address => uint256) public stakedBalances;
    mapping(address => uint256) public stakingTimestamps;
    mapping(address => uint256) public rewardsClaimed;
    
    uint256 public stakingRewardRate = 500; // 5% annual reward (500/10000)
    uint256 public constant STAKING_PERIOD = 30 days;
    uint256 public totalStaked;
    
    // Marketplace integration
    mapping(address => bool) public authorizedMarketplaces;
    mapping(address => uint256) public marketplaceVolume;
    
    // Events
    event TokensStaked(address indexed user, uint256 amount);
    event TokensUnstaked(address indexed user, uint256 amount);
    event RewardsClaimed(address indexed user, uint256 amount);
    event FeeCollected(address indexed from, address indexed to, uint256 amount);
    event MarketplaceAuthorized(address indexed marketplace, bool authorized);
    event FeeRateUpdated(uint256 oldRate, uint256 newRate);
    
    // Modifiers
    modifier onlyAuthorizedMarketplace() {
        require(authorizedMarketplaces[msg.sender], "NRC: Not authorized marketplace");
        _;
    }
    
    constructor(
        address _feeCollector
    ) ERC20("NeuroCoin", "NRC") {
        require(_feeCollector != address(0), "NRC: Invalid fee collector");
        
        feeCollector = _feeCollector;
        
        // Mint initial supply to contract deployer
        _mint(msg.sender, INITIAL_SUPPLY);
        
        // Authorize deployer as initial marketplace
        authorizedMarketplaces[msg.sender] = true;
        
        emit MarketplaceAuthorized(msg.sender, true);
    }
    
    /**
     * @dev Returns the number of decimals used for token amounts
     */
    function decimals() public pure override returns (uint8) {
        return DECIMALS;
    }
    
    /**
     * @dev Mint new tokens (only owner, respecting max supply)
     */
    function mint(address to, uint256 amount) external onlyOwner {
        require(totalSupply() + amount <= MAX_SUPPLY, "NRC: Exceeds max supply");
        _mint(to, amount);
    }
    
    /**
     * @dev Pause all token transfers (emergency function)
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause token transfers
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Update transaction fee rate
     */
    function setTransactionFeeRate(uint256 _feeRate) external onlyOwner {
        require(_feeRate <= MAX_FEE_RATE, "NRC: Fee rate too high");
        
        uint256 oldRate = transactionFeeRate;
        transactionFeeRate = _feeRate;
        
        emit FeeRateUpdated(oldRate, _feeRate);
    }
    
    /**
     * @dev Update fee collector address
     */
    function setFeeCollector(address _feeCollector) external onlyOwner {
        require(_feeCollector != address(0), "NRC: Invalid fee collector");
        feeCollector = _feeCollector;
    }
    
    /**
     * @dev Authorize/deauthorize marketplace contracts
     */
    function setMarketplaceAuthorization(address marketplace, bool authorized) external onlyOwner {
        require(marketplace != address(0), "NRC: Invalid marketplace address");
        
        authorizedMarketplaces[marketplace] = authorized;
        emit MarketplaceAuthorized(marketplace, authorized);
    }
    
    /**
     * @dev Stake tokens to earn rewards
     */
    function stakeTokens(uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "NRC: Amount must be greater than 0");
        require(balanceOf(msg.sender) >= amount, "NRC: Insufficient balance");
        
        // Claim any pending rewards first
        if (stakedBalances[msg.sender] > 0) {
            _claimRewards();
        }
        
        // Transfer tokens to contract
        _transfer(msg.sender, address(this), amount);
        
        // Update staking records
        stakedBalances[msg.sender] += amount;
        stakingTimestamps[msg.sender] = block.timestamp;
        totalStaked += amount;
        
        emit TokensStaked(msg.sender, amount);
    }
    
    /**
     * @dev Unstake tokens and claim rewards
     */
    function unstakeTokens(uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "NRC: Amount must be greater than 0");
        require(stakedBalances[msg.sender] >= amount, "NRC: Insufficient staked balance");
        require(
            block.timestamp >= stakingTimestamps[msg.sender] + STAKING_PERIOD,
            "NRC: Staking period not completed"
        );
        
        // Claim rewards first
        _claimRewards();
        
        // Update staking records
        stakedBalances[msg.sender] -= amount;
        totalStaked -= amount;
        
        // Transfer tokens back to user
        _transfer(address(this), msg.sender, amount);
        
        emit TokensUnstaked(msg.sender, amount);
    }
    
    /**
     * @dev Claim staking rewards
     */
    function claimRewards() external nonReentrant whenNotPaused {
        require(stakedBalances[msg.sender] > 0, "NRC: No staked tokens");
        _claimRewards();
    }
    
    /**
     * @dev Internal function to calculate and distribute rewards
     */
    function _claimRewards() internal {
        uint256 stakedAmount = stakedBalances[msg.sender];
        uint256 stakingDuration = block.timestamp - stakingTimestamps[msg.sender];
        
        if (stakingDuration >= STAKING_PERIOD) {
            uint256 rewardAmount = (stakedAmount * stakingRewardRate * stakingDuration) / 
                                 (10000 * 365 days);
            
            if (rewardAmount > 0 && totalSupply() + rewardAmount <= MAX_SUPPLY) {
                _mint(msg.sender, rewardAmount);
                rewardsClaimed[msg.sender] += rewardAmount;
                stakingTimestamps[msg.sender] = block.timestamp;
                
                emit RewardsClaimed(msg.sender, rewardAmount);
            }
        }
    }
    
    /**
     * @dev Calculate pending rewards for a user
     */
    function calculatePendingRewards(address user) external view returns (uint256) {
        if (stakedBalances[user] == 0) return 0;
        
        uint256 stakingDuration = block.timestamp - stakingTimestamps[user];
        if (stakingDuration < STAKING_PERIOD) return 0;
        
        return (stakedBalances[user] * stakingRewardRate * stakingDuration) / 
               (10000 * 365 days);
    }
    
    /**
     * @dev Marketplace function to transfer tokens with fee collection
     */
    function marketplaceTransfer(
        address from,
        address to,
        uint256 amount
    ) external onlyAuthorizedMarketplace nonReentrant returns (bool) {
        require(from != address(0) && to != address(0), "NRC: Invalid addresses");
        require(amount > 0, "NRC: Amount must be greater than 0");
        
        uint256 feeAmount = (amount * transactionFeeRate) / 10000;
        uint256 transferAmount = amount - feeAmount;
        
        // Transfer main amount
        _transfer(from, to, transferAmount);
        
        // Transfer fee to collector
        if (feeAmount > 0) {
            _transfer(from, feeCollector, feeAmount);
            emit FeeCollected(from, feeCollector, feeAmount);
        }
        
        // Update marketplace volume
        marketplaceVolume[msg.sender] += amount;
        
        return true;
    }
    
    /**
     * @dev Batch transfer function for airdrops or bulk payments
     */
    function batchTransfer(
        address[] calldata recipients,
        uint256[] calldata amounts
    ) external nonReentrant whenNotPaused {
        require(recipients.length == amounts.length, "NRC: Arrays length mismatch");
        require(recipients.length <= 200, "NRC: Too many recipients");
        
        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), "NRC: Invalid recipient");
            require(amounts[i] > 0, "NRC: Invalid amount");
            
            _transfer(msg.sender, recipients[i], amounts[i]);
        }
    }
    
    /**
     * @dev Emergency withdrawal function (only owner)
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        if (token == address(0)) {
            // Withdraw ETH
            payable(owner()).transfer(amount);
        } else {
            // Withdraw ERC-20 tokens
            IERC20(token).transfer(owner(), amount);
        }
    }
    
    /**
     * @dev Get comprehensive user information
     */
    function getUserInfo(address user) external view returns (
        uint256 balance,
        uint256 stakedBalance,
        uint256 pendingRewards,
        uint256 totalRewardsClaimed,
        uint256 stakingTimestamp
    ) {
        balance = balanceOf(user);
        stakedBalance = stakedBalances[user];
        totalRewardsClaimed = rewardsClaimed[user];
        stakingTimestamp = stakingTimestamps[user];
        
        // Calculate pending rewards
        if (stakedBalance > 0) {
            uint256 stakingDuration = block.timestamp - stakingTimestamp;
            if (stakingDuration >= STAKING_PERIOD) {
                pendingRewards = (stakedBalance * stakingRewardRate * stakingDuration) / 
                               (10000 * 365 days);
            }
        }
    }
    
    /**
     * @dev Override required by Solidity for multiple inheritance
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20, ERC20Pausable) {
        super._beforeTokenTransfer(from, to, amount);
    }
    
    /**
     * @dev Receive function to accept ETH
     */
    receive() external payable {
        // Allow contract to receive ETH
    }
}

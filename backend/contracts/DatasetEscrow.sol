// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title DatasetEscrow
 * @dev Escrow system for secure dataset transactions on NeuroData platform
 */
contract DatasetEscrow is Ownable, ReentrancyGuard {
    IERC20 public ncrToken;
    
    // Escrow states
    enum EscrowState {
        Active,      // Funds locked, waiting for confirmation
        Completed,   // Buyer confirmed, funds released to seller
        Disputed,    // Buyer disputed, waiting for resolution
        Refunded,    // Dispute resolved in favor of buyer
        Cancelled    // Cancelled before completion
    }
    
    // Escrow structure
    struct Escrow {
        uint256 id;
        address buyer;
        address seller;
        uint256 amount;
        string datasetId;
        EscrowState state;
        uint256 createdAt;
        uint256 autoReleaseTime;
        bool buyerConfirmed;
        bool sellerDelivered;
        string disputeReason;
        address validator;
    }
    
    // Platform settings
    uint256 public escrowFeePercent = 100; // 1% (100 basis points)
    uint256 public autoReleaseDelay = 24 hours; // Auto-release after 24 hours
    uint256 public disputeWindow = 7 days; // Dispute window
    
    // Storage
    mapping(uint256 => Escrow) public escrows;
    mapping(address => bool) public validators;
    mapping(string => uint256) public datasetToEscrow; // datasetId => escrowId
    
    uint256 public nextEscrowId = 1;
    uint256 public totalEscrowFees;
    
    // Events
    event EscrowCreated(
        uint256 indexed escrowId,
        address indexed buyer,
        address indexed seller,
        uint256 amount,
        string datasetId
    );
    
    event EscrowCompleted(
        uint256 indexed escrowId,
        address indexed buyer,
        address indexed seller,
        uint256 amount
    );
    
    event EscrowDisputed(
        uint256 indexed escrowId,
        address indexed buyer,
        string reason
    );
    
    event DisputeResolved(
        uint256 indexed escrowId,
        address indexed resolver,
        bool buyerWins
    );
    
    event EscrowRefunded(
        uint256 indexed escrowId,
        address indexed buyer,
        uint256 amount
    );
    
    event ValidatorAdded(address indexed validator);
    event ValidatorRemoved(address indexed validator);
    
    constructor(address _ncrToken) {
        ncrToken = IERC20(_ncrToken);
    }
    
    modifier onlyValidator() {
        require(validators[msg.sender] || msg.sender == owner(), "Not authorized validator");
        _;
    }
    
    modifier onlyBuyer(uint256 _escrowId) {
        require(escrows[_escrowId].buyer == msg.sender, "Only buyer can call this");
        _;
    }
    
    modifier onlySeller(uint256 _escrowId) {
        require(escrows[_escrowId].seller == msg.sender, "Only seller can call this");
        _;
    }
    
    modifier escrowExists(uint256 _escrowId) {
        require(escrows[_escrowId].id != 0, "Escrow does not exist");
        _;
    }
    
    /**
     * @dev Create new escrow for dataset purchase
     */
    function createEscrow(
        address _seller,
        uint256 _amount,
        string memory _datasetId
    ) external nonReentrant returns (uint256) {
        require(_seller != address(0), "Invalid seller address");
        require(_amount > 0, "Amount must be greater than 0");
        require(bytes(_datasetId).length > 0, "Dataset ID required");
        require(datasetToEscrow[_datasetId] == 0, "Escrow already exists for this dataset");
        
        // Transfer NCR tokens from buyer to this contract
        require(
            ncrToken.transferFrom(msg.sender, address(this), _amount),
            "Token transfer failed"
        );
        
        uint256 escrowId = nextEscrowId++;
        
        escrows[escrowId] = Escrow({
            id: escrowId,
            buyer: msg.sender,
            seller: _seller,
            amount: _amount,
            datasetId: _datasetId,
            state: EscrowState.Active,
            createdAt: block.timestamp,
            autoReleaseTime: block.timestamp + autoReleaseDelay,
            buyerConfirmed: false,
            sellerDelivered: false,
            disputeReason: "",
            validator: address(0)
        });
        
        datasetToEscrow[_datasetId] = escrowId;
        
        emit EscrowCreated(escrowId, msg.sender, _seller, _amount, _datasetId);
        
        return escrowId;
    }
    
    /**
     * @dev Seller confirms dataset delivery
     */
    function confirmDelivery(uint256 _escrowId) 
        external 
        escrowExists(_escrowId) 
        onlySeller(_escrowId) 
    {
        Escrow storage escrow = escrows[_escrowId];
        require(escrow.state == EscrowState.Active, "Escrow not active");
        
        escrow.sellerDelivered = true;
    }
    
    /**
     * @dev Buyer confirms receipt and quality of dataset
     */
    function confirmReceipt(uint256 _escrowId) 
        external 
        escrowExists(_escrowId) 
        onlyBuyer(_escrowId) 
    {
        Escrow storage escrow = escrows[_escrowId];
        require(escrow.state == EscrowState.Active, "Escrow not active");
        require(escrow.sellerDelivered, "Seller has not confirmed delivery");
        
        escrow.buyerConfirmed = true;
        escrow.state = EscrowState.Completed;
        
        _releasePayment(_escrowId);
    }
    
    /**
     * @dev Buyer disputes the transaction
     */
    function disputeTransaction(uint256 _escrowId, string memory _reason) 
        external 
        escrowExists(_escrowId) 
        onlyBuyer(_escrowId) 
    {
        Escrow storage escrow = escrows[_escrowId];
        require(escrow.state == EscrowState.Active, "Escrow not active");
        require(block.timestamp <= escrow.createdAt + disputeWindow, "Dispute window closed");
        
        escrow.state = EscrowState.Disputed;
        escrow.disputeReason = _reason;
        
        emit EscrowDisputed(_escrowId, msg.sender, _reason);
    }
    
    /**
     * @dev Auto-release payment after timeout (if no disputes)
     */
    function autoReleasePayment(uint256 _escrowId) 
        external 
        escrowExists(_escrowId) 
    {
        Escrow storage escrow = escrows[_escrowId];
        require(escrow.state == EscrowState.Active, "Escrow not active");
        require(block.timestamp >= escrow.autoReleaseTime, "Auto-release time not reached");
        require(escrow.sellerDelivered, "Seller has not confirmed delivery");
        
        escrow.state = EscrowState.Completed;
        _releasePayment(_escrowId);
    }
    
    /**
     * @dev Validator resolves dispute
     */
    function resolveDispute(uint256 _escrowId, bool _buyerWins, string memory _resolution) 
        external 
        escrowExists(_escrowId) 
        onlyValidator 
    {
        Escrow storage escrow = escrows[_escrowId];
        require(escrow.state == EscrowState.Disputed, "Escrow not disputed");
        
        escrow.validator = msg.sender;
        
        if (_buyerWins) {
            escrow.state = EscrowState.Refunded;
            _refundBuyer(_escrowId);
        } else {
            escrow.state = EscrowState.Completed;
            _releasePayment(_escrowId);
        }
        
        emit DisputeResolved(_escrowId, msg.sender, _buyerWins);
    }
    
    /**
     * @dev Internal function to release payment to seller
     */
    function _releasePayment(uint256 _escrowId) internal {
        Escrow storage escrow = escrows[_escrowId];
        
        uint256 fee = (escrow.amount * escrowFeePercent) / 10000;
        uint256 sellerAmount = escrow.amount - fee;
        
        totalEscrowFees += fee;
        
        require(
            ncrToken.transfer(escrow.seller, sellerAmount),
            "Payment transfer failed"
        );
        
        emit EscrowCompleted(_escrowId, escrow.buyer, escrow.seller, sellerAmount);
    }
    
    /**
     * @dev Internal function to refund buyer
     */
    function _refundBuyer(uint256 _escrowId) internal {
        Escrow storage escrow = escrows[_escrowId];
        
        require(
            ncrToken.transfer(escrow.buyer, escrow.amount),
            "Refund transfer failed"
        );
        
        emit EscrowRefunded(_escrowId, escrow.buyer, escrow.amount);
    }
    
    /**
     * @dev Emergency cancel escrow (only owner, for extreme cases)
     */
    function emergencyCancel(uint256 _escrowId) 
        external 
        onlyOwner 
        escrowExists(_escrowId) 
    {
        Escrow storage escrow = escrows[_escrowId];
        require(escrow.state == EscrowState.Active, "Escrow not active");
        
        escrow.state = EscrowState.Cancelled;
        _refundBuyer(_escrowId);
    }
    
    /**
     * @dev Add validator
     */
    function addValidator(address _validator) external onlyOwner {
        validators[_validator] = true;
        emit ValidatorAdded(_validator);
    }
    
    /**
     * @dev Remove validator
     */
    function removeValidator(address _validator) external onlyOwner {
        validators[_validator] = false;
        emit ValidatorRemoved(_validator);
    }
    
    /**
     * @dev Update escrow settings
     */
    function updateSettings(
        uint256 _escrowFeePercent,
        uint256 _autoReleaseDelay,
        uint256 _disputeWindow
    ) external onlyOwner {
        require(_escrowFeePercent <= 500, "Fee too high"); // Max 5%
        escrowFeePercent = _escrowFeePercent;
        autoReleaseDelay = _autoReleaseDelay;
        disputeWindow = _disputeWindow;
    }
    
    /**
     * @dev Withdraw accumulated fees
     */
    function withdrawFees() external onlyOwner {
        uint256 fees = totalEscrowFees;
        totalEscrowFees = 0;
        
        require(
            ncrToken.transfer(owner(), fees),
            "Fee withdrawal failed"
        );
    }
    
    /**
     * @dev Get escrow details
     */
    function getEscrow(uint256 _escrowId) 
        external 
        view 
        returns (
            address buyer,
            address seller,
            uint256 amount,
            string memory datasetId,
            EscrowState state,
            uint256 createdAt,
            uint256 autoReleaseTime,
            bool buyerConfirmed,
            bool sellerDelivered,
            string memory disputeReason
        ) 
    {
        Escrow storage escrow = escrows[_escrowId];
        return (
            escrow.buyer,
            escrow.seller,
            escrow.amount,
            escrow.datasetId,
            escrow.state,
            escrow.createdAt,
            escrow.autoReleaseTime,
            escrow.buyerConfirmed,
            escrow.sellerDelivered,
            escrow.disputeReason
        );
    }
    
    /**
     * @dev Get escrow ID by dataset ID
     */
    function getEscrowByDataset(string memory _datasetId) 
        external 
        view 
        returns (uint256) 
    {
        return datasetToEscrow[_datasetId];
    }
    
    /**
     * @dev Check if escrow can be auto-released
     */
    function canAutoRelease(uint256 _escrowId) 
        external 
        view 
        returns (bool) 
    {
        Escrow storage escrow = escrows[_escrowId];
        return (
            escrow.state == EscrowState.Active &&
            escrow.sellerDelivered &&
            block.timestamp >= escrow.autoReleaseTime
        );
    }
}

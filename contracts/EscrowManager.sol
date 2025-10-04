// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "./NeuroCoin.sol";

/**
 * @title EscrowManager
 * @dev Advanced escrow system for secure dataset transactions
 * 
 * Features:
 * - Multi-party escrow support
 * - Milestone-based releases
 * - Automated dispute resolution
 * - Emergency recovery mechanisms
 * - Fee distribution system
 */
contract EscrowManager is ReentrancyGuard, Ownable, Pausable {
    using Counters for Counters.Counter;
    
    NeuroCoin public immutable neuroCoin;
    Counters.Counter private _escrowIds;
    
    // Configuration
    uint256 public defaultEscrowPeriod = 7 days;
    uint256 public maxEscrowPeriod = 90 days;
    uint256 public disputeWindow = 14 days;
    uint256 public arbitrationFee = 1000; // 10% of disputed amount
    address public arbitrator;
    
    // Escrow structure
    struct Escrow {
        uint256 id;
        address buyer;
        address seller;
        address arbitrator;
        uint256 amount;
        uint256 releaseTime;
        EscrowStatus status;
        string description;
        bytes32 dataHash; // Hash of the data being sold
        uint256 createdAt;
        uint256 completedAt;
        Milestone[] milestones;
        uint256 releasedAmount;
        mapping(address => bool) hasApproved;
        uint256 approvalCount;
    }
    
    // Milestone structure for complex transactions
    struct Milestone {
        string description;
        uint256 amount;
        bool isCompleted;
        uint256 completedAt;
        address completedBy;
    }
    
    // Dispute structure
    struct DisputeInfo {
        uint256 escrowId;
        address initiator;
        string reason;
        uint256 createdAt;
        DisputeStatus status;
        uint256 votingDeadline;
        mapping(address => Vote) votes;
        address[] voters;
        uint256 buyerVotes;
        uint256 sellerVotes;
    }
    
    struct Vote {
        bool hasVoted;
        bool supportsBuyer;
        string reason;
        uint256 timestamp;
    }
    
    // Enums
    enum EscrowStatus {
        Active,
        Completed,
        Disputed,
        Cancelled,
        Refunded
    }
    
    enum DisputeStatus {
        Open,
        Voting,
        Resolved,
        Escalated
    }
    
    // Mappings
    mapping(uint256 => Escrow) public escrows;
    mapping(uint256 => DisputeInfo) public disputes;
    mapping(address => uint256[]) public userEscrows;
    mapping(address => bool) public authorizedArbitrators;
    mapping(bytes32 => bool) public usedDataHashes;
    
    // Events
    event EscrowCreated(
        uint256 indexed escrowId,
        address indexed buyer,
        address indexed seller,
        uint256 amount,
        uint256 releaseTime
    );
    
    event EscrowCompleted(
        uint256 indexed escrowId,
        address indexed buyer,
        address indexed seller,
        uint256 amount
    );
    
    event EscrowDisputed(
        uint256 indexed escrowId,
        address indexed initiator,
        string reason
    );
    
    event DisputeResolved(
        uint256 indexed escrowId,
        address winner,
        uint256 amount
    );
    
    event MilestoneCompleted(
        uint256 indexed escrowId,
        uint256 milestoneIndex,
        address completedBy,
        uint256 amount
    );
    
    event EscrowApproved(
        uint256 indexed escrowId,
        address indexed approver
    );
    
    event ArbitratorChanged(
        address indexed oldArbitrator,
        address indexed newArbitrator
    );
    
    // Modifiers
    modifier onlyEscrowParty(uint256 escrowId) {
        Escrow storage escrow = escrows[escrowId];
        require(
            msg.sender == escrow.buyer || 
            msg.sender == escrow.seller || 
            msg.sender == escrow.arbitrator,
            "Not authorized"
        );
        _;
    }
    
    modifier onlyArbitrator() {
        require(authorizedArbitrators[msg.sender] || msg.sender == arbitrator, "Not arbitrator");
        _;
    }
    
    modifier escrowExists(uint256 escrowId) {
        require(escrows[escrowId].id != 0, "Escrow does not exist");
        _;
    }
    
    constructor(
        address _neuroCoin,
        address _arbitrator
    ) {
        require(_neuroCoin != address(0), "Invalid NeuroCoin address");
        require(_arbitrator != address(0), "Invalid arbitrator address");
        
        neuroCoin = NeuroCoin(_neuroCoin);
        arbitrator = _arbitrator;
        authorizedArbitrators[_arbitrator] = true;
    }
    
    /**
     * @dev Create a new escrow
     */
    function createEscrow(
        address seller,
        uint256 amount,
        uint256 escrowPeriod,
        string calldata description,
        bytes32 dataHash
    ) external whenNotPaused nonReentrant returns (uint256) {
        require(seller != address(0) && seller != msg.sender, "Invalid seller");
        require(amount > 0, "Amount must be greater than 0");
        require(escrowPeriod <= maxEscrowPeriod, "Escrow period too long");
        require(!usedDataHashes[dataHash], "Data hash already used");
        
        // Transfer tokens to escrow
        require(
            neuroCoin.transferFrom(msg.sender, address(this), amount),
            "Token transfer failed"
        );
        
        _escrowIds.increment();
        uint256 escrowId = _escrowIds.current();
        
        uint256 releaseTime = block.timestamp + (escrowPeriod > 0 ? escrowPeriod : defaultEscrowPeriod);
        
        Escrow storage newEscrow = escrows[escrowId];
        newEscrow.id = escrowId;
        newEscrow.buyer = msg.sender;
        newEscrow.seller = seller;
        newEscrow.arbitrator = arbitrator;
        newEscrow.amount = amount;
        newEscrow.releaseTime = releaseTime;
        newEscrow.status = EscrowStatus.Active;
        newEscrow.description = description;
        newEscrow.dataHash = dataHash;
        newEscrow.createdAt = block.timestamp;
        newEscrow.releasedAmount = 0;
        newEscrow.approvalCount = 0;
        
        userEscrows[msg.sender].push(escrowId);
        userEscrows[seller].push(escrowId);
        usedDataHashes[dataHash] = true;
        
        emit EscrowCreated(escrowId, msg.sender, seller, amount, releaseTime);
        
        return escrowId;
    }
    
    /**
     * @dev Create escrow with milestones
     */
    function createMilestoneEscrow(
        address seller,
        uint256 totalAmount,
        uint256 escrowPeriod,
        string calldata description,
        bytes32 dataHash,
        string[] calldata milestoneDescriptions,
        uint256[] calldata milestoneAmounts
    ) external whenNotPaused nonReentrant returns (uint256) {
        require(milestoneDescriptions.length == milestoneAmounts.length, "Array length mismatch");
        require(milestoneDescriptions.length > 0, "No milestones provided");
        require(milestoneDescriptions.length <= 10, "Too many milestones");
        
        // Verify total amount matches sum of milestones
        uint256 sum = 0;
        for (uint256 i = 0; i < milestoneAmounts.length; i++) {
            require(milestoneAmounts[i] > 0, "Invalid milestone amount");
            sum += milestoneAmounts[i];
        }
        require(sum == totalAmount, "Milestone amounts don't match total");
        
        uint256 escrowId = createEscrow(seller, totalAmount, escrowPeriod, description, dataHash);
        
        // Add milestones
        for (uint256 i = 0; i < milestoneDescriptions.length; i++) {
            escrows[escrowId].milestones.push(Milestone({
                description: milestoneDescriptions[i],
                amount: milestoneAmounts[i],
                isCompleted: false,
                completedAt: 0,
                completedBy: address(0)
            }));
        }
        
        return escrowId;
    }
    
    /**
     * @dev Approve escrow release (both parties must approve)
     */
    function approveEscrow(uint256 escrowId) external escrowExists(escrowId) onlyEscrowParty(escrowId) {
        Escrow storage escrow = escrows[escrowId];
        require(escrow.status == EscrowStatus.Active, "Escrow not active");
        require(!escrow.hasApproved[msg.sender], "Already approved");
        
        escrow.hasApproved[msg.sender] = true;
        escrow.approvalCount++;
        
        emit EscrowApproved(escrowId, msg.sender);
        
        // If both parties approved, complete the escrow
        if (escrow.approvalCount >= 2) {
            _completeEscrow(escrowId);
        }
    }
    
    /**
     * @dev Complete a milestone
     */
    function completeMilestone(
        uint256 escrowId,
        uint256 milestoneIndex
    ) external escrowExists(escrowId) onlyEscrowParty(escrowId) {
        Escrow storage escrow = escrows[escrowId];
        require(escrow.status == EscrowStatus.Active, "Escrow not active");
        require(milestoneIndex < escrow.milestones.length, "Invalid milestone index");
        require(!escrow.milestones[milestoneIndex].isCompleted, "Milestone already completed");
        
        // Only seller can mark milestones as completed
        require(msg.sender == escrow.seller, "Only seller can complete milestones");
        
        Milestone storage milestone = escrow.milestones[milestoneIndex];
        milestone.isCompleted = true;
        milestone.completedAt = block.timestamp;
        milestone.completedBy = msg.sender;
        
        // Release milestone payment
        escrow.releasedAmount += milestone.amount;
        require(
            neuroCoin.transfer(escrow.seller, milestone.amount),
            "Milestone payment failed"
        );
        
        emit MilestoneCompleted(escrowId, milestoneIndex, msg.sender, milestone.amount);
        
        // Check if all milestones are completed
        bool allCompleted = true;
        for (uint256 i = 0; i < escrow.milestones.length; i++) {
            if (!escrow.milestones[i].isCompleted) {
                allCompleted = false;
                break;
            }
        }
        
        if (allCompleted) {
            escrow.status = EscrowStatus.Completed;
            escrow.completedAt = block.timestamp;
            emit EscrowCompleted(escrowId, escrow.buyer, escrow.seller, escrow.amount);
        }
    }
    
    /**
     * @dev Release escrow funds (automatic after release time)
     */
    function releaseEscrow(uint256 escrowId) external nonReentrant escrowExists(escrowId) {
        Escrow storage escrow = escrows[escrowId];
        require(escrow.status == EscrowStatus.Active, "Escrow not active");
        require(
            block.timestamp >= escrow.releaseTime || 
            msg.sender == escrow.buyer ||
            escrow.approvalCount >= 2,
            "Cannot release yet"
        );
        
        _completeEscrow(escrowId);
    }
    
    /**
     * @dev Internal function to complete escrow
     */
    function _completeEscrow(uint256 escrowId) internal {
        Escrow storage escrow = escrows[escrowId];
        
        escrow.status = EscrowStatus.Completed;
        escrow.completedAt = block.timestamp;
        
        uint256 remainingAmount = escrow.amount - escrow.releasedAmount;
        if (remainingAmount > 0) {
            require(
                neuroCoin.transfer(escrow.seller, remainingAmount),
                "Transfer to seller failed"
            );
        }
        
        emit EscrowCompleted(escrowId, escrow.buyer, escrow.seller, escrow.amount);
    }
    
    /**
     * @dev Create a dispute
     */
    function createDispute(
        uint256 escrowId,
        string calldata reason
    ) external escrowExists(escrowId) onlyEscrowParty(escrowId) {
        Escrow storage escrow = escrows[escrowId];
        require(escrow.status == EscrowStatus.Active, "Escrow not active");
        require(
            block.timestamp <= escrow.releaseTime + disputeWindow,
            "Dispute window expired"
        );
        
        escrow.status = EscrowStatus.Disputed;
        
        DisputeInfo storage dispute = disputes[escrowId];
        dispute.escrowId = escrowId;
        dispute.initiator = msg.sender;
        dispute.reason = reason;
        dispute.createdAt = block.timestamp;
        dispute.status = DisputeStatus.Open;
        dispute.votingDeadline = block.timestamp + 7 days;
        
        emit EscrowDisputed(escrowId, msg.sender, reason);
    }
    
    /**
     * @dev Vote on a dispute (community voting)
     */
    function voteOnDispute(
        uint256 escrowId,
        bool supportsBuyer,
        string calldata reason
    ) external escrowExists(escrowId) {
        DisputeInfo storage dispute = disputes[escrowId];
        require(dispute.status == DisputeStatus.Open, "Dispute not open for voting");
        require(block.timestamp <= dispute.votingDeadline, "Voting period ended");
        require(!dispute.votes[msg.sender].hasVoted, "Already voted");
        require(msg.sender != escrows[escrowId].buyer && msg.sender != escrows[escrowId].seller, "Parties cannot vote");
        
        // Require minimum NRC balance to vote (prevent spam)
        require(neuroCoin.balanceOf(msg.sender) >= 1000 * 10**18, "Insufficient NRC balance to vote");
        
        dispute.votes[msg.sender] = Vote({
            hasVoted: true,
            supportsBuyer: supportsBuyer,
            reason: reason,
            timestamp: block.timestamp
        });
        
        dispute.voters.push(msg.sender);
        
        if (supportsBuyer) {
            dispute.buyerVotes++;
        } else {
            dispute.sellerVotes++;
        }
        
        // Auto-resolve if enough votes
        if (dispute.voters.length >= 10) {
            _resolveDisputeByVoting(escrowId);
        }
    }
    
    /**
     * @dev Resolve dispute by voting results
     */
    function _resolveDisputeByVoting(uint256 escrowId) internal {
        DisputeInfo storage dispute = disputes[escrowId];
        Escrow storage escrow = escrows[escrowId];
        
        dispute.status = DisputeStatus.Resolved;
        
        if (dispute.buyerVotes > dispute.sellerVotes) {
            // Refund to buyer
            escrow.status = EscrowStatus.Refunded;
            require(
                neuroCoin.transfer(escrow.buyer, escrow.amount),
                "Refund failed"
            );
            emit DisputeResolved(escrowId, escrow.buyer, escrow.amount);
        } else {
            // Release to seller
            escrow.status = EscrowStatus.Completed;
            escrow.completedAt = block.timestamp;
            require(
                neuroCoin.transfer(escrow.seller, escrow.amount),
                "Release to seller failed"
            );
            emit DisputeResolved(escrowId, escrow.seller, escrow.amount);
        }
    }
    
    /**
     * @dev Arbitrator resolves dispute
     */
    function resolveDispute(
        uint256 escrowId,
        bool refundToBuyer,
        string calldata resolution
    ) external onlyArbitrator escrowExists(escrowId) {
        Escrow storage escrow = escrows[escrowId];
        DisputeInfo storage dispute = disputes[escrowId];
        
        require(escrow.status == EscrowStatus.Disputed, "Not disputed");
        
        dispute.status = DisputeStatus.Resolved;
        
        uint256 arbitrationFeeAmount = (escrow.amount * arbitrationFee) / 10000;
        uint256 remainingAmount = escrow.amount - arbitrationFeeAmount;
        
        // Pay arbitration fee
        require(
            neuroCoin.transfer(msg.sender, arbitrationFeeAmount),
            "Arbitration fee transfer failed"
        );
        
        if (refundToBuyer) {
            escrow.status = EscrowStatus.Refunded;
            require(
                neuroCoin.transfer(escrow.buyer, remainingAmount),
                "Refund failed"
            );
            emit DisputeResolved(escrowId, escrow.buyer, remainingAmount);
        } else {
            escrow.status = EscrowStatus.Completed;
            escrow.completedAt = block.timestamp;
            require(
                neuroCoin.transfer(escrow.seller, remainingAmount),
                "Release to seller failed"
            );
            emit DisputeResolved(escrowId, escrow.seller, remainingAmount);
        }
    }
    
    /**
     * @dev Cancel escrow (only before seller acceptance)
     */
    function cancelEscrow(uint256 escrowId) external escrowExists(escrowId) {
        Escrow storage escrow = escrows[escrowId];
        require(msg.sender == escrow.buyer, "Only buyer can cancel");
        require(escrow.status == EscrowStatus.Active, "Escrow not active");
        require(escrow.approvalCount == 0, "Cannot cancel after approvals");
        require(block.timestamp <= escrow.createdAt + 1 hours, "Cancellation period expired");
        
        escrow.status = EscrowStatus.Cancelled;
        
        require(
            neuroCoin.transfer(escrow.buyer, escrow.amount),
            "Refund failed"
        );
    }
    
    /**
     * @dev Get escrow details
     */
    function getEscrowDetails(uint256 escrowId) external view returns (
        address buyer,
        address seller,
        uint256 amount,
        EscrowStatus status,
        uint256 releaseTime,
        string memory description,
        uint256 milestonesCount,
        uint256 releasedAmount
    ) {
        Escrow storage escrow = escrows[escrowId];
        return (
            escrow.buyer,
            escrow.seller,
            escrow.amount,
            escrow.status,
            escrow.releaseTime,
            escrow.description,
            escrow.milestones.length,
            escrow.releasedAmount
        );
    }
    
    /**
     * @dev Get milestone details
     */
    function getMilestone(uint256 escrowId, uint256 milestoneIndex) external view returns (
        string memory description,
        uint256 amount,
        bool isCompleted,
        uint256 completedAt,
        address completedBy
    ) {
        require(milestoneIndex < escrows[escrowId].milestones.length, "Invalid milestone index");
        Milestone storage milestone = escrows[escrowId].milestones[milestoneIndex];
        return (
            milestone.description,
            milestone.amount,
            milestone.isCompleted,
            milestone.completedAt,
            milestone.completedBy
        );
    }
    
    /**
     * @dev Get user's escrows
     */
    function getUserEscrows(address user) external view returns (uint256[] memory) {
        return userEscrows[user];
    }
    
    /**
     * @dev Admin functions
     */
    function setArbitrator(address _arbitrator) external onlyOwner {
        require(_arbitrator != address(0), "Invalid arbitrator");
        address oldArbitrator = arbitrator;
        arbitrator = _arbitrator;
        authorizedArbitrators[_arbitrator] = true;
        emit ArbitratorChanged(oldArbitrator, _arbitrator);
    }
    
    function setAuthorizedArbitrator(address _arbitrator, bool _authorized) external onlyOwner {
        authorizedArbitrators[_arbitrator] = _authorized;
    }
    
    function setDefaultEscrowPeriod(uint256 _period) external onlyOwner {
        require(_period >= 1 days && _period <= maxEscrowPeriod, "Invalid period");
        defaultEscrowPeriod = _period;
    }
    
    function setArbitrationFee(uint256 _fee) external onlyOwner {
        require(_fee <= 2000, "Fee too high"); // Max 20%
        arbitrationFee = _fee;
    }
    
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Emergency functions
     */
    function emergencyWithdraw(uint256 amount) external onlyOwner {
        require(neuroCoin.transfer(owner(), amount), "Transfer failed");
    }
}

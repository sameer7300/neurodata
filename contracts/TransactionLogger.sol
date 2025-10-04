// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title TransactionLogger
 * @dev Comprehensive transaction logging and analytics for the NeuroData ecosystem
 * 
 * Features:
 * - Transaction logging with detailed metadata
 * - Analytics and reporting
 * - Revenue tracking
 * - User activity monitoring
 * - Gas optimization for bulk operations
 */
contract TransactionLogger is Ownable, Pausable {
    using Counters for Counters.Counter;
    
    Counters.Counter private _transactionIds;
    
    // Transaction types
    enum TransactionType {
        DatasetPurchase,
        DatasetSale,
        EscrowCreation,
        EscrowRelease,
        DisputeCreation,
        DisputeResolution,
        StakingReward,
        TokenTransfer,
        PlatformFee,
        Refund
    }
    
    // Transaction status
    enum TransactionStatus {
        Pending,
        Completed,
        Failed,
        Cancelled
    }
    
    // Transaction structure
    struct Transaction {
        uint256 id;
        TransactionType txType;
        address from;
        address to;
        uint256 amount;
        uint256 timestamp;
        TransactionStatus status;
        bytes32 dataHash; // Hash of associated data
        string metadata; // JSON metadata
        uint256 gasUsed;
        uint256 blockNumber;
        bytes32 txHash;
    }
    
    // Analytics structures
    struct DailyStats {
        uint256 date; // Unix timestamp (start of day)
        uint256 totalTransactions;
        uint256 totalVolume;
        uint256 totalFees;
        uint256 uniqueUsers;
        mapping(TransactionType => uint256) transactionsByType;
        mapping(TransactionType => uint256) volumeByType;
    }
    
    struct UserStats {
        uint256 totalTransactions;
        uint256 totalVolume;
        uint256 totalSpent;
        uint256 totalEarned;
        uint256 firstTransactionTime;
        uint256 lastTransactionTime;
        mapping(TransactionType => uint256) transactionsByType;
    }
    
    // Mappings
    mapping(uint256 => Transaction) public transactions;
    mapping(address => uint256[]) public userTransactions;
    mapping(bytes32 => uint256[]) public transactionsByHash;
    mapping(uint256 => DailyStats) public dailyStats; // date => stats
    mapping(address => UserStats) public userStats;
    mapping(address => bool) public authorizedLoggers;
    
    // Analytics data
    uint256 public totalTransactions;
    uint256 public totalVolume;
    uint256 public totalFees;
    uint256 public totalUniqueUsers;
    
    // Events
    event TransactionLogged(
        uint256 indexed transactionId,
        TransactionType indexed txType,
        address indexed from,
        address to,
        uint256 amount
    );
    
    event DailyStatsUpdated(
        uint256 indexed date,
        uint256 totalTransactions,
        uint256 totalVolume
    );
    
    event LoggerAuthorized(address indexed logger, bool authorized);
    
    // Modifiers
    modifier onlyAuthorizedLogger() {
        require(authorizedLoggers[msg.sender] || msg.sender == owner(), "Not authorized logger");
        _;
    }
    
    constructor() {
        authorizedLoggers[msg.sender] = true;
    }
    
    /**
     * @dev Log a new transaction
     */
    function logTransaction(
        TransactionType txType,
        address from,
        address to,
        uint256 amount,
        bytes32 dataHash,
        string calldata metadata
    ) external onlyAuthorizedLogger whenNotPaused returns (uint256) {
        _transactionIds.increment();
        uint256 transactionId = _transactionIds.current();
        
        transactions[transactionId] = Transaction({
            id: transactionId,
            txType: txType,
            from: from,
            to: to,
            amount: amount,
            timestamp: block.timestamp,
            status: TransactionStatus.Pending,
            dataHash: dataHash,
            metadata: metadata,
            gasUsed: 0,
            blockNumber: block.number,
            txHash: blockhash(block.number - 1)
        });
        
        // Update user transactions
        userTransactions[from].push(transactionId);
        if (to != address(0) && to != from) {
            userTransactions[to].push(transactionId);
        }
        
        // Update hash mapping
        if (dataHash != bytes32(0)) {
            transactionsByHash[dataHash].push(transactionId);
        }
        
        emit TransactionLogged(transactionId, txType, from, to, amount);
        
        return transactionId;
    }
    
    /**
     * @dev Update transaction status
     */
    function updateTransactionStatus(
        uint256 transactionId,
        TransactionStatus status,
        uint256 gasUsed
    ) external onlyAuthorizedLogger {
        require(transactions[transactionId].id != 0, "Transaction does not exist");
        
        Transaction storage txn = transactions[transactionId];
        txn.status = status;
        txn.gasUsed = gasUsed;
        
        // Update analytics only for completed transactions
        if (status == TransactionStatus.Completed) {
            _updateAnalytics(txn);
        }
    }
    
    /**
     * @dev Batch log multiple transactions (gas optimized)
     */
    function batchLogTransactions(
        TransactionType[] calldata txTypes,
        address[] calldata froms,
        address[] calldata tos,
        uint256[] calldata amounts,
        bytes32[] calldata dataHashes,
        string[] calldata metadatas
    ) external onlyAuthorizedLogger whenNotPaused returns (uint256[] memory) {
        require(
            txTypes.length == froms.length &&
            froms.length == tos.length &&
            tos.length == amounts.length &&
            amounts.length == dataHashes.length &&
            dataHashes.length == metadatas.length,
            "Array length mismatch"
        );
        require(txTypes.length <= 100, "Too many transactions");
        
        uint256[] memory transactionIds = new uint256[](txTypes.length);
        
        for (uint256 i = 0; i < txTypes.length; i++) {
            _transactionIds.increment();
            uint256 transactionId = _transactionIds.current();
            
            transactions[transactionId] = Transaction({
                id: transactionId,
                txType: txTypes[i],
                from: froms[i],
                to: tos[i],
                amount: amounts[i],
                timestamp: block.timestamp,
                status: TransactionStatus.Completed, // Assume completed for batch
                dataHash: dataHashes[i],
                metadata: metadatas[i],
                gasUsed: 0,
                blockNumber: block.number,
                txHash: blockhash(block.number - 1)
            });
            
            transactionIds[i] = transactionId;
            
            // Update user transactions
            userTransactions[froms[i]].push(transactionId);
            if (tos[i] != address(0) && tos[i] != froms[i]) {
                userTransactions[tos[i]].push(transactionId);
            }
            
            // Update hash mapping
            if (dataHashes[i] != bytes32(0)) {
                transactionsByHash[dataHashes[i]].push(transactionId);
            }
            
            // Update analytics
            _updateAnalytics(transactions[transactionId]);
            
            emit TransactionLogged(transactionId, txTypes[i], froms[i], tos[i], amounts[i]);
        }
        
        return transactionIds;
    }
    
    /**
     * @dev Internal function to update analytics
     */
    function _updateAnalytics(Transaction storage txn) internal {
        // Update global stats
        totalTransactions++;
        totalVolume += txn.amount;
        
        // Calculate platform fees (assuming 2.5% fee)
        if (txn.txType == TransactionType.DatasetPurchase) {
            uint256 fee = (txn.amount * 250) / 10000;
            totalFees += fee;
        }
        
        // Update daily stats
        uint256 dayStart = (txn.timestamp / 1 days) * 1 days;
        DailyStats storage dayStats = dailyStats[dayStart];
        
        if (dayStats.date == 0) {
            dayStats.date = dayStart;
        }
        
        dayStats.totalTransactions++;
        dayStats.totalVolume += txn.amount;
        dayStats.transactionsByType[txn.txType]++;
        dayStats.volumeByType[txn.txType] += txn.amount;
        
        // Update user stats
        UserStats storage fromStats = userStats[txn.from];
        if (fromStats.firstTransactionTime == 0) {
            fromStats.firstTransactionTime = txn.timestamp;
            totalUniqueUsers++;
        }
        fromStats.lastTransactionTime = txn.timestamp;
        fromStats.totalTransactions++;
        fromStats.totalVolume += txn.amount;
        fromStats.transactionsByType[txn.txType]++;
        
        // Update spent/earned based on transaction type
        if (txn.txType == TransactionType.DatasetPurchase) {
            fromStats.totalSpent += txn.amount;
        } else if (txn.txType == TransactionType.DatasetSale) {
            fromStats.totalEarned += txn.amount;
        }
        
        // Update recipient stats if different from sender
        if (txn.to != address(0) && txn.to != txn.from) {
            UserStats storage toStats = userStats[txn.to];
            if (toStats.firstTransactionTime == 0) {
                toStats.firstTransactionTime = txn.timestamp;
                totalUniqueUsers++;
            }
            toStats.lastTransactionTime = txn.timestamp;
            toStats.totalTransactions++;
            toStats.totalVolume += txn.amount;
            
            if (txn.txType == TransactionType.DatasetPurchase) {
                toStats.totalEarned += txn.amount;
            }
        }
        
        emit DailyStatsUpdated(dayStart, dayStats.totalTransactions, dayStats.totalVolume);
    }
    
    /**
     * @dev Get transaction details
     */
    function getTransaction(uint256 transactionId) external view returns (
        TransactionType txType,
        address from,
        address to,
        uint256 amount,
        uint256 timestamp,
        TransactionStatus status,
        string memory metadata
    ) {
        Transaction storage txn = transactions[transactionId];
        return (
            txn.txType,
            txn.from,
            txn.to,
            txn.amount,
            txn.timestamp,
            txn.status,
            txn.metadata
        );
    }
    
    /**
     * @dev Get user's transaction history
     */
    function getUserTransactions(
        address user,
        uint256 offset,
        uint256 limit
    ) external view returns (uint256[] memory) {
        uint256[] storage userTxs = userTransactions[user];
        require(offset < userTxs.length, "Offset out of bounds");
        
        uint256 end = offset + limit;
        if (end > userTxs.length) {
            end = userTxs.length;
        }
        
        uint256[] memory result = new uint256[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            result[i - offset] = userTxs[i];
        }
        
        return result;
    }
    
    /**
     * @dev Get transactions by data hash
     */
    function getTransactionsByHash(bytes32 dataHash) external view returns (uint256[] memory) {
        return transactionsByHash[dataHash];
    }
    
    /**
     * @dev Get daily statistics
     */
    function getDailyStats(uint256 date) external view returns (
        uint256 totalTransactions,
        uint256 totalVolume,
        uint256 totalFees,
        uint256 uniqueUsers
    ) {
        DailyStats storage stats = dailyStats[date];
        return (
            stats.totalTransactions,
            stats.totalVolume,
            stats.totalFees,
            stats.uniqueUsers
        );
    }
    
    /**
     * @dev Get daily stats by transaction type
     */
    function getDailyStatsByType(
        uint256 date,
        TransactionType txType
    ) external view returns (uint256 transactions, uint256 volume) {
        DailyStats storage stats = dailyStats[date];
        return (
            stats.transactionsByType[txType],
            stats.volumeByType[txType]
        );
    }
    
    /**
     * @dev Get user statistics
     */
    function getUserStats(address user) external view returns (
        uint256 totalTransactions,
        uint256 totalVolume,
        uint256 totalSpent,
        uint256 totalEarned,
        uint256 firstTransactionTime,
        uint256 lastTransactionTime
    ) {
        UserStats storage stats = userStats[user];
        return (
            stats.totalTransactions,
            stats.totalVolume,
            stats.totalSpent,
            stats.totalEarned,
            stats.firstTransactionTime,
            stats.lastTransactionTime
        );
    }
    
    /**
     * @dev Get user stats by transaction type
     */
    function getUserStatsByType(
        address user,
        TransactionType txType
    ) external view returns (uint256) {
        return userStats[user].transactionsByType[txType];
    }
    
    /**
     * @dev Get platform analytics
     */
    function getPlatformAnalytics() external view returns (
        uint256 _totalTransactions,
        uint256 _totalVolume,
        uint256 _totalFees,
        uint256 _totalUniqueUsers
    ) {
        return (
            totalTransactions,
            totalVolume,
            totalFees,
            totalUniqueUsers
        );
    }
    
    /**
     * @dev Get top users by volume (expensive operation, use carefully)
     */
    function getTopUsersByVolume(
        address[] calldata users,
        uint256 limit
    ) external view returns (address[] memory, uint256[] memory) {
        require(limit <= users.length && limit <= 100, "Invalid limit");
        
        // Simple bubble sort for demonstration (use more efficient sorting in production)
        address[] memory sortedUsers = new address[](users.length);
        uint256[] memory volumes = new uint256[](users.length);
        
        for (uint256 i = 0; i < users.length; i++) {
            sortedUsers[i] = users[i];
            volumes[i] = userStats[users[i]].totalVolume;
        }
        
        // Sort by volume (descending)
        for (uint256 i = 0; i < users.length - 1; i++) {
            for (uint256 j = 0; j < users.length - i - 1; j++) {
                if (volumes[j] < volumes[j + 1]) {
                    // Swap volumes
                    uint256 tempVolume = volumes[j];
                    volumes[j] = volumes[j + 1];
                    volumes[j + 1] = tempVolume;
                    
                    // Swap addresses
                    address tempAddr = sortedUsers[j];
                    sortedUsers[j] = sortedUsers[j + 1];
                    sortedUsers[j + 1] = tempAddr;
                }
            }
        }
        
        // Return top users
        address[] memory topUsers = new address[](limit);
        uint256[] memory topVolumes = new uint256[](limit);
        
        for (uint256 i = 0; i < limit; i++) {
            topUsers[i] = sortedUsers[i];
            topVolumes[i] = volumes[i];
        }
        
        return (topUsers, topVolumes);
    }
    
    /**
     * @dev Generate analytics report for date range
     */
    function getAnalyticsReport(
        uint256 startDate,
        uint256 endDate
    ) external view returns (
        uint256 totalTxs,
        uint256 totalVol,
        uint256 avgDailyTxs,
        uint256 avgDailyVol
    ) {
        require(startDate <= endDate, "Invalid date range");
        require(endDate <= block.timestamp, "End date in future");
        
        uint256 days = 0;
        totalTxs = 0;
        totalVol = 0;
        
        for (uint256 date = startDate; date <= endDate; date += 1 days) {
            uint256 dayStart = (date / 1 days) * 1 days;
            DailyStats storage dayStats = dailyStats[dayStart];
            
            if (dayStats.date != 0) {
                totalTxs += dayStats.totalTransactions;
                totalVol += dayStats.totalVolume;
                days++;
            }
        }
        
        if (days > 0) {
            avgDailyTxs = totalTxs / days;
            avgDailyVol = totalVol / days;
        }
    }
    
    /**
     * @dev Admin functions
     */
    function setAuthorizedLogger(address logger, bool authorized) external onlyOwner {
        authorizedLoggers[logger] = authorized;
        emit LoggerAuthorized(logger, authorized);
    }
    
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Emergency function to clean up old data (gas optimization)
     */
    function cleanupOldTransactions(uint256[] calldata transactionIds) external onlyOwner {
        for (uint256 i = 0; i < transactionIds.length; i++) {
            delete transactions[transactionIds[i]];
        }
    }
}

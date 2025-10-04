// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "./NeuroCoin.sol";

/**
 * @title DatasetMarketplace
 * @dev Smart contract for decentralized dataset trading using NeuroCoin (NRC)
 * 
 * Features:
 * - Dataset listing and purchasing
 * - Escrow mechanism for secure transactions
 * - Revenue sharing between platform and sellers
 * - Dispute resolution system
 * - Quality scoring and reputation system
 * - Bulk purchase discounts
 */
contract DatasetMarketplace is ReentrancyGuard, Ownable, Pausable {
    using Counters for Counters.Counter;
    
    // State variables
    NeuroCoin public immutable neuroCoin;
    Counters.Counter private _datasetIds;
    Counters.Counter private _purchaseIds;
    
    // Platform configuration
    uint256 public platformFeeRate = 250; // 2.5% (250/10000)
    uint256 public constant MAX_PLATFORM_FEE = 1000; // 10% maximum
    address public platformFeeRecipient;
    
    // Escrow configuration
    uint256 public escrowPeriod = 7 days;
    uint256 public disputePeriod = 14 days;
    
    // Dataset structure
    struct Dataset {
        uint256 id;
        address seller;
        string ipfsHash;
        string metadataHash;
        uint256 price;
        string title;
        string description;
        string[] tags;
        uint256 fileSize;
        string fileType;
        bool isActive;
        uint256 totalSales;
        uint256 totalRevenue;
        uint256 createdAt;
        uint256 updatedAt;
        uint8 qualityScore; // 0-100
    }
    
    // Purchase structure
    struct Purchase {
        uint256 id;
        uint256 datasetId;
        address buyer;
        address seller;
        uint256 amount;
        uint256 platformFee;
        uint256 sellerAmount;
        PurchaseStatus status;
        uint256 createdAt;
        uint256 escrowReleaseTime;
        string buyerReview;
        uint8 rating; // 1-5 stars
    }
    
    // Dispute structure
    struct Dispute {
        uint256 purchaseId;
        address initiator;
        string reason;
        DisputeStatus status;
        uint256 createdAt;
        uint256 resolvedAt;
        address resolver;
        string resolution;
    }
    
    // Enums
    enum PurchaseStatus {
        Pending,
        InEscrow,
        Completed,
        Disputed,
        Refunded,
        Cancelled
    }
    
    enum DisputeStatus {
        Open,
        UnderReview,
        Resolved,
        Closed
    }
    
    // Mappings
    mapping(uint256 => Dataset) public datasets;
    mapping(uint256 => Purchase) public purchases;
    mapping(uint256 => Dispute) public disputes;
    mapping(address => uint256[]) public sellerDatasets;
    mapping(address => uint256[]) public buyerPurchases;
    mapping(address => mapping(uint256 => bool)) public hasPurchased;
    mapping(address => uint256) public sellerRatings; // Total rating points
    mapping(address => uint256) public sellerRatingCounts; // Number of ratings
    mapping(bytes32 => bool) public usedIPFSHashes; // Prevent duplicate uploads
    
    // Bulk purchase discounts
    mapping(uint256 => uint256) public bulkDiscounts; // quantity => discount rate (basis points)
    
    // Events
    event DatasetListed(
        uint256 indexed datasetId,
        address indexed seller,
        string ipfsHash,
        uint256 price,
        string title
    );
    
    event DatasetUpdated(
        uint256 indexed datasetId,
        uint256 newPrice,
        bool isActive
    );
    
    event DatasetPurchased(
        uint256 indexed purchaseId,
        uint256 indexed datasetId,
        address indexed buyer,
        address seller,
        uint256 amount
    );
    
    event PurchaseCompleted(
        uint256 indexed purchaseId,
        uint256 indexed datasetId,
        address indexed buyer
    );
    
    event DisputeCreated(
        uint256 indexed purchaseId,
        address indexed initiator,
        string reason
    );
    
    event DisputeResolved(
        uint256 indexed purchaseId,
        address indexed resolver,
        string resolution
    );
    
    event EscrowReleased(
        uint256 indexed purchaseId,
        address indexed seller,
        uint256 amount
    );
    
    event ReviewSubmitted(
        uint256 indexed purchaseId,
        address indexed buyer,
        uint8 rating,
        string review
    );
    
    // Modifiers
    modifier onlyDatasetSeller(uint256 datasetId) {
        require(datasets[datasetId].seller == msg.sender, "Not dataset seller");
        _;
    }
    
    modifier onlyPurchaseBuyer(uint256 purchaseId) {
        require(purchases[purchaseId].buyer == msg.sender, "Not purchase buyer");
        _;
    }
    
    modifier datasetExists(uint256 datasetId) {
        require(datasets[datasetId].id != 0, "Dataset does not exist");
        _;
    }
    
    modifier purchaseExists(uint256 purchaseId) {
        require(purchases[purchaseId].id != 0, "Purchase does not exist");
        _;
    }
    
    constructor(
        address _neuroCoin,
        address _platformFeeRecipient
    ) {
        require(_neuroCoin != address(0), "Invalid NeuroCoin address");
        require(_platformFeeRecipient != address(0), "Invalid fee recipient");
        
        neuroCoin = NeuroCoin(_neuroCoin);
        platformFeeRecipient = _platformFeeRecipient;
        
        // Set default bulk discounts
        bulkDiscounts[5] = 500;   // 5% discount for 5+ datasets
        bulkDiscounts[10] = 1000; // 10% discount for 10+ datasets
        bulkDiscounts[25] = 1500; // 15% discount for 25+ datasets
    }
    
    /**
     * @dev List a new dataset for sale
     */
    function listDataset(
        string calldata ipfsHash,
        string calldata metadataHash,
        uint256 price,
        string calldata title,
        string calldata description,
        string[] calldata tags,
        uint256 fileSize,
        string calldata fileType
    ) external whenNotPaused nonReentrant returns (uint256) {
        require(bytes(ipfsHash).length > 0, "IPFS hash required");
        require(bytes(title).length > 0, "Title required");
        require(price > 0, "Price must be greater than 0");
        require(tags.length <= 10, "Too many tags");
        
        bytes32 hashKey = keccak256(abi.encodePacked(ipfsHash));
        require(!usedIPFSHashes[hashKey], "Dataset already exists");
        
        _datasetIds.increment();
        uint256 datasetId = _datasetIds.current();
        
        datasets[datasetId] = Dataset({
            id: datasetId,
            seller: msg.sender,
            ipfsHash: ipfsHash,
            metadataHash: metadataHash,
            price: price,
            title: title,
            description: description,
            tags: tags,
            fileSize: fileSize,
            fileType: fileType,
            isActive: true,
            totalSales: 0,
            totalRevenue: 0,
            createdAt: block.timestamp,
            updatedAt: block.timestamp,
            qualityScore: 50 // Default quality score
        });
        
        sellerDatasets[msg.sender].push(datasetId);
        usedIPFSHashes[hashKey] = true;
        
        emit DatasetListed(datasetId, msg.sender, ipfsHash, price, title);
        
        return datasetId;
    }
    
    /**
     * @dev Update dataset information
     */
    function updateDataset(
        uint256 datasetId,
        uint256 newPrice,
        string calldata newDescription,
        bool isActive
    ) external datasetExists(datasetId) onlyDatasetSeller(datasetId) {
        Dataset storage dataset = datasets[datasetId];
        
        if (newPrice > 0) {
            dataset.price = newPrice;
        }
        
        if (bytes(newDescription).length > 0) {
            dataset.description = newDescription;
        }
        
        dataset.isActive = isActive;
        dataset.updatedAt = block.timestamp;
        
        emit DatasetUpdated(datasetId, newPrice, isActive);
    }
    
    /**
     * @dev Purchase a dataset
     */
    function purchaseDataset(
        uint256 datasetId
    ) external whenNotPaused nonReentrant datasetExists(datasetId) returns (uint256) {
        Dataset storage dataset = datasets[datasetId];
        require(dataset.isActive, "Dataset not active");
        require(dataset.seller != msg.sender, "Cannot buy own dataset");
        require(!hasPurchased[msg.sender][datasetId], "Already purchased");
        
        uint256 totalAmount = dataset.price;
        uint256 platformFee = (totalAmount * platformFeeRate) / 10000;
        uint256 sellerAmount = totalAmount - platformFee;
        
        // Transfer tokens to escrow (this contract)
        require(
            neuroCoin.transferFrom(msg.sender, address(this), totalAmount),
            "Token transfer failed"
        );
        
        _purchaseIds.increment();
        uint256 purchaseId = _purchaseIds.current();
        
        purchases[purchaseId] = Purchase({
            id: purchaseId,
            datasetId: datasetId,
            buyer: msg.sender,
            seller: dataset.seller,
            amount: totalAmount,
            platformFee: platformFee,
            sellerAmount: sellerAmount,
            status: PurchaseStatus.InEscrow,
            createdAt: block.timestamp,
            escrowReleaseTime: block.timestamp + escrowPeriod,
            buyerReview: "",
            rating: 0
        });
        
        buyerPurchases[msg.sender].push(purchaseId);
        hasPurchased[msg.sender][datasetId] = true;
        
        // Update dataset statistics
        dataset.totalSales++;
        dataset.totalRevenue += totalAmount;
        
        emit DatasetPurchased(purchaseId, datasetId, msg.sender, dataset.seller, totalAmount);
        
        return purchaseId;
    }
    
    /**
     * @dev Bulk purchase multiple datasets with discount
     */
    function bulkPurchaseDatasets(
        uint256[] calldata datasetIds
    ) external whenNotPaused nonReentrant returns (uint256[] memory) {
        require(datasetIds.length > 1, "Use single purchase for one dataset");
        require(datasetIds.length <= 50, "Too many datasets");
        
        uint256 totalAmount = 0;
        
        // Calculate total amount
        for (uint256 i = 0; i < datasetIds.length; i++) {
            Dataset storage dataset = datasets[datasetIds[i]];
            require(dataset.id != 0, "Dataset does not exist");
            require(dataset.isActive, "Dataset not active");
            require(dataset.seller != msg.sender, "Cannot buy own dataset");
            require(!hasPurchased[msg.sender][datasetIds[i]], "Already purchased dataset");
            
            totalAmount += dataset.price;
        }
        
        // Apply bulk discount
        uint256 discountRate = getBulkDiscountRate(datasetIds.length);
        if (discountRate > 0) {
            uint256 discount = (totalAmount * discountRate) / 10000;
            totalAmount -= discount;
        }
        
        // Transfer total amount to escrow
        require(
            neuroCoin.transferFrom(msg.sender, address(this), totalAmount),
            "Token transfer failed"
        );
        
        uint256[] memory purchaseIds = new uint256[](datasetIds.length);
        
        // Create individual purchases
        for (uint256 i = 0; i < datasetIds.length; i++) {
            Dataset storage dataset = datasets[datasetIds[i]];
            
            uint256 datasetPrice = dataset.price;
            if (discountRate > 0) {
                uint256 discount = (datasetPrice * discountRate) / 10000;
                datasetPrice -= discount;
            }
            
            uint256 platformFee = (datasetPrice * platformFeeRate) / 10000;
            uint256 sellerAmount = datasetPrice - platformFee;
            
            _purchaseIds.increment();
            uint256 purchaseId = _purchaseIds.current();
            
            purchases[purchaseId] = Purchase({
                id: purchaseId,
                datasetId: datasetIds[i],
                buyer: msg.sender,
                seller: dataset.seller,
                amount: datasetPrice,
                platformFee: platformFee,
                sellerAmount: sellerAmount,
                status: PurchaseStatus.InEscrow,
                createdAt: block.timestamp,
                escrowReleaseTime: block.timestamp + escrowPeriod,
                buyerReview: "",
                rating: 0
            });
            
            purchaseIds[i] = purchaseId;
            buyerPurchases[msg.sender].push(purchaseId);
            hasPurchased[msg.sender][datasetIds[i]] = true;
            
            // Update dataset statistics
            dataset.totalSales++;
            dataset.totalRevenue += datasetPrice;
            
            emit DatasetPurchased(purchaseId, datasetIds[i], msg.sender, dataset.seller, datasetPrice);
        }
        
        return purchaseIds;
    }
    
    /**
     * @dev Release escrow funds to seller (automatic after escrow period)
     */
    function releaseEscrow(
        uint256 purchaseId
    ) external nonReentrant purchaseExists(purchaseId) {
        Purchase storage purchase = purchases[purchaseId];
        require(purchase.status == PurchaseStatus.InEscrow, "Not in escrow");
        require(
            block.timestamp >= purchase.escrowReleaseTime || 
            msg.sender == purchase.buyer,
            "Escrow period not ended"
        );
        
        purchase.status = PurchaseStatus.Completed;
        
        // Transfer funds
        require(
            neuroCoin.transfer(purchase.seller, purchase.sellerAmount),
            "Seller transfer failed"
        );
        
        require(
            neuroCoin.transfer(platformFeeRecipient, purchase.platformFee),
            "Platform fee transfer failed"
        );
        
        emit EscrowReleased(purchaseId, purchase.seller, purchase.sellerAmount);
        emit PurchaseCompleted(purchaseId, purchase.datasetId, purchase.buyer);
    }
    
    /**
     * @dev Submit a review and rating for a completed purchase
     */
    function submitReview(
        uint256 purchaseId,
        uint8 rating,
        string calldata review
    ) external purchaseExists(purchaseId) onlyPurchaseBuyer(purchaseId) {
        Purchase storage purchase = purchases[purchaseId];
        require(purchase.status == PurchaseStatus.Completed, "Purchase not completed");
        require(rating >= 1 && rating <= 5, "Rating must be 1-5");
        require(purchase.rating == 0, "Review already submitted");
        
        purchase.rating = rating;
        purchase.buyerReview = review;
        
        // Update seller rating
        sellerRatings[purchase.seller] += rating;
        sellerRatingCounts[purchase.seller]++;
        
        // Update dataset quality score
        Dataset storage dataset = datasets[purchase.datasetId];
        uint256 newScore = (uint256(dataset.qualityScore) + rating * 20) / 2; // Convert 1-5 to 20-100 scale
        dataset.qualityScore = uint8(newScore > 100 ? 100 : newScore);
        
        emit ReviewSubmitted(purchaseId, msg.sender, rating, review);
    }
    
    /**
     * @dev Create a dispute for a purchase
     */
    function createDispute(
        uint256 purchaseId,
        string calldata reason
    ) external purchaseExists(purchaseId) {
        Purchase storage purchase = purchases[purchaseId];
        require(
            msg.sender == purchase.buyer || msg.sender == purchase.seller,
            "Not authorized"
        );
        require(purchase.status == PurchaseStatus.InEscrow, "Not in escrow");
        require(
            block.timestamp <= purchase.escrowReleaseTime + disputePeriod,
            "Dispute period expired"
        );
        
        purchase.status = PurchaseStatus.Disputed;
        
        disputes[purchaseId] = Dispute({
            purchaseId: purchaseId,
            initiator: msg.sender,
            reason: reason,
            status: DisputeStatus.Open,
            createdAt: block.timestamp,
            resolvedAt: 0,
            resolver: address(0),
            resolution: ""
        });
        
        emit DisputeCreated(purchaseId, msg.sender, reason);
    }
    
    /**
     * @dev Resolve a dispute (only owner)
     */
    function resolveDispute(
        uint256 purchaseId,
        bool refundToBuyer,
        string calldata resolution
    ) external onlyOwner purchaseExists(purchaseId) {
        Purchase storage purchase = purchases[purchaseId];
        Dispute storage dispute = disputes[purchaseId];
        
        require(purchase.status == PurchaseStatus.Disputed, "Not disputed");
        require(dispute.status == DisputeStatus.Open, "Dispute not open");
        
        if (refundToBuyer) {
            purchase.status = PurchaseStatus.Refunded;
            require(
                neuroCoin.transfer(purchase.buyer, purchase.amount),
                "Refund transfer failed"
            );
        } else {
            purchase.status = PurchaseStatus.Completed;
            require(
                neuroCoin.transfer(purchase.seller, purchase.sellerAmount),
                "Seller transfer failed"
            );
            require(
                neuroCoin.transfer(platformFeeRecipient, purchase.platformFee),
                "Platform fee transfer failed"
            );
        }
        
        dispute.status = DisputeStatus.Resolved;
        dispute.resolvedAt = block.timestamp;
        dispute.resolver = msg.sender;
        dispute.resolution = resolution;
        
        emit DisputeResolved(purchaseId, msg.sender, resolution);
    }
    
    /**
     * @dev Get bulk discount rate based on quantity
     */
    function getBulkDiscountRate(uint256 quantity) public view returns (uint256) {
        if (quantity >= 25) return bulkDiscounts[25];
        if (quantity >= 10) return bulkDiscounts[10];
        if (quantity >= 5) return bulkDiscounts[5];
        return 0;
    }
    
    /**
     * @dev Get seller's average rating
     */
    function getSellerRating(address seller) external view returns (uint256 avgRating, uint256 totalRatings) {
        totalRatings = sellerRatingCounts[seller];
        if (totalRatings > 0) {
            avgRating = sellerRatings[seller] / totalRatings;
        }
    }
    
    /**
     * @dev Get dataset information
     */
    function getDataset(uint256 datasetId) external view returns (Dataset memory) {
        return datasets[datasetId];
    }
    
    /**
     * @dev Get purchase information
     */
    function getPurchase(uint256 purchaseId) external view returns (Purchase memory) {
        return purchases[purchaseId];
    }
    
    /**
     * @dev Get user's datasets
     */
    function getSellerDatasets(address seller) external view returns (uint256[] memory) {
        return sellerDatasets[seller];
    }
    
    /**
     * @dev Get user's purchases
     */
    function getBuyerPurchases(address buyer) external view returns (uint256[] memory) {
        return buyerPurchases[buyer];
    }
    
    /**
     * @dev Admin functions
     */
    function setPlatformFeeRate(uint256 _feeRate) external onlyOwner {
        require(_feeRate <= MAX_PLATFORM_FEE, "Fee rate too high");
        platformFeeRate = _feeRate;
    }
    
    function setPlatformFeeRecipient(address _recipient) external onlyOwner {
        require(_recipient != address(0), "Invalid recipient");
        platformFeeRecipient = _recipient;
    }
    
    function setEscrowPeriod(uint256 _period) external onlyOwner {
        require(_period >= 1 days && _period <= 30 days, "Invalid period");
        escrowPeriod = _period;
    }
    
    function setBulkDiscount(uint256 quantity, uint256 discountRate) external onlyOwner {
        require(discountRate <= 2000, "Discount too high"); // Max 20%
        bulkDiscounts[quantity] = discountRate;
    }
    
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Emergency withdrawal (only owner)
     */
    function emergencyWithdraw(uint256 amount) external onlyOwner {
        require(neuroCoin.transfer(owner(), amount), "Transfer failed");
    }
}

const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("DatasetMarketplace", function () {
  // Fixture for deploying contracts
  async function deployMarketplaceFixture() {
    const [owner, seller, buyer, platformFeeRecipient] = await ethers.getSigners();
    
    // Deploy NeuroCoin first
    const NeuroCoin = await ethers.getContractFactory("NeuroCoin");
    const neuroCoin = await NeuroCoin.deploy(platformFeeRecipient.address);
    
    // Deploy DatasetMarketplace
    const DatasetMarketplace = await ethers.getContractFactory("DatasetMarketplace");
    const marketplace = await DatasetMarketplace.deploy(
      neuroCoin.address,
      platformFeeRecipient.address
    );
    
    // Authorize marketplace in NeuroCoin
    await neuroCoin.setMarketplaceAuthorization(marketplace.address, true);
    
    // Give some tokens to buyer and seller
    const tokenAmount = ethers.utils.parseEther("10000");
    await neuroCoin.transfer(buyer.address, tokenAmount);
    await neuroCoin.transfer(seller.address, tokenAmount);
    
    return { 
      neuroCoin, 
      marketplace, 
      owner, 
      seller, 
      buyer, 
      platformFeeRecipient 
    };
  }
  
  describe("Deployment", function () {
    it("Should set the correct NeuroCoin address", async function () {
      const { neuroCoin, marketplace } = await loadFixture(deployMarketplaceFixture);
      
      expect(await marketplace.neuroCoin()).to.equal(neuroCoin.address);
    });
    
    it("Should set the correct platform fee recipient", async function () {
      const { marketplace, platformFeeRecipient } = await loadFixture(deployMarketplaceFixture);
      
      expect(await marketplace.platformFeeRecipient()).to.equal(platformFeeRecipient.address);
    });
    
    it("Should set default platform fee rate", async function () {
      const { marketplace } = await loadFixture(deployMarketplaceFixture);
      
      expect(await marketplace.platformFeeRate()).to.equal(250); // 2.5%
    });
    
    it("Should set default bulk discounts", async function () {
      const { marketplace } = await loadFixture(deployMarketplaceFixture);
      
      expect(await marketplace.bulkDiscounts(5)).to.equal(500);   // 5%
      expect(await marketplace.bulkDiscounts(10)).to.equal(1000); // 10%
      expect(await marketplace.bulkDiscounts(25)).to.equal(1500); // 15%
    });
  });
  
  describe("Dataset Listing", function () {
    it("Should allow users to list datasets", async function () {
      const { marketplace, seller } = await loadFixture(deployMarketplaceFixture);
      
      const datasetData = {
        ipfsHash: "QmTestHash123",
        metadataHash: "QmMetaHash456",
        price: ethers.utils.parseEther("100"),
        title: "Test Dataset",
        description: "A test dataset for unit testing",
        tags: ["test", "data", "ml"],
        fileSize: 1024000,
        fileType: "csv"
      };
      
      await expect(
        marketplace.connect(seller).listDataset(
          datasetData.ipfsHash,
          datasetData.metadataHash,
          datasetData.price,
          datasetData.title,
          datasetData.description,
          datasetData.tags,
          datasetData.fileSize,
          datasetData.fileType
        )
      ).to.emit(marketplace, "DatasetListed")
        .withArgs(1, seller.address, datasetData.ipfsHash, datasetData.price, datasetData.title);
      
      const dataset = await marketplace.getDataset(1);
      expect(dataset.seller).to.equal(seller.address);
      expect(dataset.title).to.equal(datasetData.title);
      expect(dataset.price).to.equal(datasetData.price);
      expect(dataset.isActive).to.be.true;
    });
    
    it("Should not allow listing with empty IPFS hash", async function () {
      const { marketplace, seller } = await loadFixture(deployMarketplaceFixture);
      
      await expect(
        marketplace.connect(seller).listDataset(
          "",
          "QmMetaHash456",
          ethers.utils.parseEther("100"),
          "Test Dataset",
          "Description",
          ["test"],
          1024000,
          "csv"
        )
      ).to.be.revertedWith("IPFS hash required");
    });
    
    it("Should not allow listing with zero price", async function () {
      const { marketplace, seller } = await loadFixture(deployMarketplaceFixture);
      
      await expect(
        marketplace.connect(seller).listDataset(
          "QmTestHash123",
          "QmMetaHash456",
          0,
          "Test Dataset",
          "Description",
          ["test"],
          1024000,
          "csv"
        )
      ).to.be.revertedWith("Price must be greater than 0");
    });
    
    it("Should not allow duplicate IPFS hashes", async function () {
      const { marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      const ipfsHash = "QmTestHash123";
      
      // First listing
      await marketplace.connect(seller).listDataset(
        ipfsHash,
        "QmMetaHash456",
        ethers.utils.parseEther("100"),
        "Test Dataset 1",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      // Second listing with same IPFS hash
      await expect(
        marketplace.connect(buyer).listDataset(
          ipfsHash,
          "QmMetaHash789",
          ethers.utils.parseEther("200"),
          "Test Dataset 2",
          "Description",
          ["test"],
          1024000,
          "csv"
        )
      ).to.be.revertedWith("Dataset already exists");
    });
  });
  
  describe("Dataset Updates", function () {
    it("Should allow dataset owner to update dataset", async function () {
      const { marketplace, seller } = await loadFixture(deployMarketplaceFixture);
      
      // List a dataset first
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        ethers.utils.parseEther("100"),
        "Test Dataset",
        "Original description",
        ["test"],
        1024000,
        "csv"
      );
      
      const newPrice = ethers.utils.parseEther("150");
      const newDescription = "Updated description";
      
      await expect(
        marketplace.connect(seller).updateDataset(1, newPrice, newDescription, true)
      ).to.emit(marketplace, "DatasetUpdated")
        .withArgs(1, newPrice, true);
      
      const dataset = await marketplace.getDataset(1);
      expect(dataset.price).to.equal(newPrice);
      expect(dataset.description).to.equal(newDescription);
    });
    
    it("Should not allow non-owner to update dataset", async function () {
      const { marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      // List a dataset
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        ethers.utils.parseEther("100"),
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      await expect(
        marketplace.connect(buyer).updateDataset(1, ethers.utils.parseEther("200"), "New desc", true)
      ).to.be.revertedWith("Not dataset seller");
    });
  });
  
  describe("Dataset Purchase", function () {
    it("Should allow users to purchase datasets", async function () {
      const { neuroCoin, marketplace, seller, buyer, platformFeeRecipient } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List a dataset
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      // Approve marketplace to spend buyer's tokens
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      
      // Purchase dataset
      await expect(
        marketplace.connect(buyer).purchaseDataset(1)
      ).to.emit(marketplace, "DatasetPurchased")
        .withArgs(1, 1, buyer.address, seller.address, price);
      
      // Check purchase record
      const purchase = await marketplace.getPurchase(1);
      expect(purchase.buyer).to.equal(buyer.address);
      expect(purchase.seller).to.equal(seller.address);
      expect(purchase.amount).to.equal(price);
      expect(purchase.status).to.equal(1); // InEscrow
      
      // Check that buyer has purchased the dataset
      expect(await marketplace.hasPurchased(buyer.address, 1)).to.be.true;
    });
    
    it("Should not allow purchasing own dataset", async function () {
      const { neuroCoin, marketplace, seller } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List a dataset
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      // Approve and try to purchase own dataset
      await neuroCoin.connect(seller).approve(marketplace.address, price);
      
      await expect(
        marketplace.connect(seller).purchaseDataset(1)
      ).to.be.revertedWith("Cannot buy own dataset");
    });
    
    it("Should not allow purchasing inactive dataset", async function () {
      const { neuroCoin, marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List a dataset
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      // Deactivate dataset
      await marketplace.connect(seller).updateDataset(1, 0, "", false);
      
      // Try to purchase inactive dataset
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      
      await expect(
        marketplace.connect(buyer).purchaseDataset(1)
      ).to.be.revertedWith("Dataset not active");
    });
    
    it("Should not allow duplicate purchases", async function () {
      const { neuroCoin, marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List a dataset
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      // First purchase
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      await marketplace.connect(buyer).purchaseDataset(1);
      
      // Try to purchase again
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      
      await expect(
        marketplace.connect(buyer).purchaseDataset(1)
      ).to.be.revertedWith("Already purchased");
    });
  });
  
  describe("Bulk Purchase", function () {
    it("Should allow bulk purchase with discount", async function () {
      const { neuroCoin, marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      const datasetIds = [];
      
      // List 5 datasets
      for (let i = 0; i < 5; i++) {
        await marketplace.connect(seller).listDataset(
          `QmTestHash${i}`,
          `QmMetaHash${i}`,
          price,
          `Test Dataset ${i}`,
          "Description",
          ["test"],
          1024000,
          "csv"
        );
        datasetIds.push(i + 1);
      }
      
      const totalPrice = price.mul(5);
      const discountRate = await marketplace.getBulkDiscountRate(5);
      const discount = totalPrice.mul(discountRate).div(10000);
      const finalPrice = totalPrice.sub(discount);
      
      // Approve and bulk purchase
      await neuroCoin.connect(buyer).approve(marketplace.address, finalPrice);
      
      const purchaseIds = await marketplace.connect(buyer).callStatic.bulkPurchaseDatasets(datasetIds);
      await marketplace.connect(buyer).bulkPurchaseDatasets(datasetIds);
      
      expect(purchaseIds.length).to.equal(5);
      
      // Check that all datasets are purchased
      for (let i = 0; i < 5; i++) {
        expect(await marketplace.hasPurchased(buyer.address, i + 1)).to.be.true;
      }
    });
    
    it("Should not allow bulk purchase of single dataset", async function () {
      const { marketplace, buyer } = await loadFixture(deployMarketplaceFixture);
      
      await expect(
        marketplace.connect(buyer).bulkPurchaseDatasets([1])
      ).to.be.revertedWith("Use single purchase for one dataset");
    });
  });
  
  describe("Escrow Release", function () {
    it("Should allow buyer to release escrow early", async function () {
      const { neuroCoin, marketplace, seller, buyer, platformFeeRecipient } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      const platformFeeRate = await marketplace.platformFeeRate();
      const platformFee = price.mul(platformFeeRate).div(10000);
      const sellerAmount = price.sub(platformFee);
      
      // List and purchase dataset
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      await marketplace.connect(buyer).purchaseDataset(1);
      
      const sellerBalanceBefore = await neuroCoin.balanceOf(seller.address);
      const feeRecipientBalanceBefore = await neuroCoin.balanceOf(platformFeeRecipient.address);
      
      // Release escrow
      await expect(
        marketplace.connect(buyer).releaseEscrow(1)
      ).to.emit(marketplace, "EscrowReleased")
        .withArgs(1, seller.address, sellerAmount);
      
      // Check balances
      const sellerBalanceAfter = await neuroCoin.balanceOf(seller.address);
      const feeRecipientBalanceAfter = await neuroCoin.balanceOf(platformFeeRecipient.address);
      
      expect(sellerBalanceAfter.sub(sellerBalanceBefore)).to.equal(sellerAmount);
      expect(feeRecipientBalanceAfter.sub(feeRecipientBalanceBefore)).to.equal(platformFee);
      
      // Check purchase status
      const purchase = await marketplace.getPurchase(1);
      expect(purchase.status).to.equal(2); // Completed
    });
    
    it("Should automatically release escrow after period", async function () {
      const { neuroCoin, marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List and purchase dataset
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      await marketplace.connect(buyer).purchaseDataset(1);
      
      // Fast forward time past escrow period
      const escrowPeriod = await marketplace.escrowPeriod();
      await ethers.provider.send("evm_increaseTime", [escrowPeriod.toNumber()]);
      await ethers.provider.send("evm_mine");
      
      // Anyone can release escrow now
      await marketplace.releaseEscrow(1);
      
      const purchase = await marketplace.getPurchase(1);
      expect(purchase.status).to.equal(2); // Completed
    });
  });
  
  describe("Reviews", function () {
    it("Should allow buyers to submit reviews", async function () {
      const { neuroCoin, marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List, purchase, and complete transaction
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      await marketplace.connect(buyer).purchaseDataset(1);
      await marketplace.connect(buyer).releaseEscrow(1);
      
      // Submit review
      const rating = 5;
      const review = "Excellent dataset!";
      
      await expect(
        marketplace.connect(buyer).submitReview(1, rating, review)
      ).to.emit(marketplace, "ReviewSubmitted")
        .withArgs(1, buyer.address, rating, review);
      
      const purchase = await marketplace.getPurchase(1);
      expect(purchase.rating).to.equal(rating);
      expect(purchase.buyerReview).to.equal(review);
    });
    
    it("Should not allow review before purchase completion", async function () {
      const { neuroCoin, marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List and purchase dataset (but don't complete)
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      await marketplace.connect(buyer).purchaseDataset(1);
      
      // Try to submit review before completion
      await expect(
        marketplace.connect(buyer).submitReview(1, 5, "Great!")
      ).to.be.revertedWith("Purchase not completed");
    });
  });
  
  describe("Disputes", function () {
    it("Should allow creating disputes", async function () {
      const { neuroCoin, marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List and purchase dataset
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      await marketplace.connect(buyer).purchaseDataset(1);
      
      const reason = "Dataset is corrupted";
      
      await expect(
        marketplace.connect(buyer).createDispute(1, reason)
      ).to.emit(marketplace, "DisputeCreated")
        .withArgs(1, buyer.address, reason);
      
      const purchase = await marketplace.getPurchase(1);
      expect(purchase.status).to.equal(3); // Disputed
    });
    
    it("Should allow owner to resolve disputes", async function () {
      const { neuroCoin, marketplace, seller, buyer, owner } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List, purchase, and create dispute
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      await marketplace.connect(buyer).purchaseDataset(1);
      await marketplace.connect(buyer).createDispute(1, "Issue with dataset");
      
      const buyerBalanceBefore = await neuroCoin.balanceOf(buyer.address);
      
      // Resolve dispute in favor of buyer (refund)
      const resolution = "Refunding buyer due to valid complaint";
      
      await expect(
        marketplace.connect(owner).resolveDispute(1, true, resolution)
      ).to.emit(marketplace, "DisputeResolved")
        .withArgs(1, owner.address, resolution);
      
      // Check refund
      const buyerBalanceAfter = await neuroCoin.balanceOf(buyer.address);
      expect(buyerBalanceAfter.sub(buyerBalanceBefore)).to.equal(price);
      
      const purchase = await marketplace.getPurchase(1);
      expect(purchase.status).to.equal(4); // Refunded
    });
  });
  
  describe("Admin Functions", function () {
    it("Should allow owner to update platform fee rate", async function () {
      const { marketplace, owner } = await loadFixture(deployMarketplaceFixture);
      
      const newFeeRate = 300; // 3%
      await marketplace.connect(owner).setPlatformFeeRate(newFeeRate);
      
      expect(await marketplace.platformFeeRate()).to.equal(newFeeRate);
    });
    
    it("Should not allow setting fee rate above maximum", async function () {
      const { marketplace, owner } = await loadFixture(deployMarketplaceFixture);
      
      const maxFee = await marketplace.MAX_PLATFORM_FEE();
      const excessiveFee = maxFee.add(1);
      
      await expect(
        marketplace.connect(owner).setPlatformFeeRate(excessiveFee)
      ).to.be.revertedWith("Fee rate too high");
    });
    
    it("Should allow owner to pause and unpause", async function () {
      const { marketplace, seller, owner } = await loadFixture(deployMarketplaceFixture);
      
      // Pause marketplace
      await marketplace.connect(owner).pause();
      
      // Try to list dataset while paused
      await expect(
        marketplace.connect(seller).listDataset(
          "QmTestHash123",
          "QmMetaHash456",
          ethers.utils.parseEther("100"),
          "Test Dataset",
          "Description",
          ["test"],
          1024000,
          "csv"
        )
      ).to.be.revertedWith("Pausable: paused");
      
      // Unpause
      await marketplace.connect(owner).unpause();
      
      // Should work now
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        ethers.utils.parseEther("100"),
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
    });
  });
  
  describe("View Functions", function () {
    it("Should return seller datasets", async function () {
      const { marketplace, seller } = await loadFixture(deployMarketplaceFixture);
      
      // List multiple datasets
      for (let i = 0; i < 3; i++) {
        await marketplace.connect(seller).listDataset(
          `QmTestHash${i}`,
          `QmMetaHash${i}`,
          ethers.utils.parseEther("100"),
          `Test Dataset ${i}`,
          "Description",
          ["test"],
          1024000,
          "csv"
        );
      }
      
      const sellerDatasets = await marketplace.getSellerDatasets(seller.address);
      expect(sellerDatasets.length).to.equal(3);
      expect(sellerDatasets[0]).to.equal(1);
      expect(sellerDatasets[1]).to.equal(2);
      expect(sellerDatasets[2]).to.equal(3);
    });
    
    it("Should return buyer purchases", async function () {
      const { neuroCoin, marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List and purchase multiple datasets
      for (let i = 0; i < 2; i++) {
        await marketplace.connect(seller).listDataset(
          `QmTestHash${i}`,
          `QmMetaHash${i}`,
          price,
          `Test Dataset ${i}`,
          "Description",
          ["test"],
          1024000,
          "csv"
        );
        
        await neuroCoin.connect(buyer).approve(marketplace.address, price);
        await marketplace.connect(buyer).purchaseDataset(i + 1);
      }
      
      const buyerPurchases = await marketplace.getBuyerPurchases(buyer.address);
      expect(buyerPurchases.length).to.equal(2);
    });
    
    it("Should return seller rating", async function () {
      const { neuroCoin, marketplace, seller, buyer } = await loadFixture(deployMarketplaceFixture);
      
      const price = ethers.utils.parseEther("100");
      
      // List, purchase, complete, and review
      await marketplace.connect(seller).listDataset(
        "QmTestHash123",
        "QmMetaHash456",
        price,
        "Test Dataset",
        "Description",
        ["test"],
        1024000,
        "csv"
      );
      
      await neuroCoin.connect(buyer).approve(marketplace.address, price);
      await marketplace.connect(buyer).purchaseDataset(1);
      await marketplace.connect(buyer).releaseEscrow(1);
      await marketplace.connect(buyer).submitReview(1, 4, "Good dataset");
      
      const [avgRating, totalRatings] = await marketplace.getSellerRating(seller.address);
      expect(avgRating).to.equal(4);
      expect(totalRatings).to.equal(1);
    });
  });
});

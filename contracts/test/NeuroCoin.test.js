const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("NeuroCoin", function () {
  // Fixture for deploying the contract
  async function deployNeuroCoinFixture() {
    const [owner, feeCollector, user1, user2, marketplace] = await ethers.getSigners();
    
    const NeuroCoin = await ethers.getContractFactory("NeuroCoin");
    const neuroCoin = await NeuroCoin.deploy(feeCollector.address);
    
    return { neuroCoin, owner, feeCollector, user1, user2, marketplace };
  }
  
  describe("Deployment", function () {
    it("Should set the right name and symbol", async function () {
      const { neuroCoin } = await loadFixture(deployNeuroCoinFixture);
      
      expect(await neuroCoin.name()).to.equal("NeuroCoin");
      expect(await neuroCoin.symbol()).to.equal("NRC");
      expect(await neuroCoin.decimals()).to.equal(18);
    });
    
    it("Should mint initial supply to owner", async function () {
      const { neuroCoin, owner } = await loadFixture(deployNeuroCoinFixture);
      
      const initialSupply = ethers.utils.parseEther("100000000"); // 100M NRC
      expect(await neuroCoin.totalSupply()).to.equal(initialSupply);
      expect(await neuroCoin.balanceOf(owner.address)).to.equal(initialSupply);
    });
    
    it("Should set the fee collector", async function () {
      const { neuroCoin, feeCollector } = await loadFixture(deployNeuroCoinFixture);
      
      expect(await neuroCoin.feeCollector()).to.equal(feeCollector.address);
    });
    
    it("Should authorize deployer as marketplace", async function () {
      const { neuroCoin, owner } = await loadFixture(deployNeuroCoinFixture);
      
      expect(await neuroCoin.authorizedMarketplaces(owner.address)).to.be.true;
    });
  });
  
  describe("Minting", function () {
    it("Should allow owner to mint tokens", async function () {
      const { neuroCoin, owner, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      const mintAmount = ethers.utils.parseEther("1000");
      await neuroCoin.mint(user1.address, mintAmount);
      
      expect(await neuroCoin.balanceOf(user1.address)).to.equal(mintAmount);
    });
    
    it("Should not allow minting beyond max supply", async function () {
      const { neuroCoin, owner, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      const maxSupply = ethers.utils.parseEther("1000000000"); // 1B NRC
      const currentSupply = await neuroCoin.totalSupply();
      const excessAmount = maxSupply.sub(currentSupply).add(1);
      
      await expect(
        neuroCoin.mint(user1.address, excessAmount)
      ).to.be.revertedWith("NRC: Exceeds max supply");
    });
    
    it("Should not allow non-owner to mint", async function () {
      const { neuroCoin, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      const mintAmount = ethers.utils.parseEther("1000");
      await expect(
        neuroCoin.connect(user1).mint(user1.address, mintAmount)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });
  
  describe("Staking", function () {
    it("Should allow users to stake tokens", async function () {
      const { neuroCoin, owner, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      const stakeAmount = ethers.utils.parseEther("1000");
      
      // Transfer tokens to user1
      await neuroCoin.transfer(user1.address, stakeAmount);
      
      // User1 stakes tokens
      await neuroCoin.connect(user1).stakeTokens(stakeAmount);
      
      expect(await neuroCoin.stakedBalances(user1.address)).to.equal(stakeAmount);
      expect(await neuroCoin.totalStaked()).to.equal(stakeAmount);
      expect(await neuroCoin.balanceOf(neuroCoin.address)).to.equal(stakeAmount);
    });
    
    it("Should not allow staking more than balance", async function () {
      const { neuroCoin, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      const stakeAmount = ethers.utils.parseEther("1000");
      
      await expect(
        neuroCoin.connect(user1).stakeTokens(stakeAmount)
      ).to.be.revertedWith("NRC: Insufficient balance");
    });
    
    it("Should allow unstaking after staking period", async function () {
      const { neuroCoin, owner, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      const stakeAmount = ethers.utils.parseEther("1000");
      
      // Transfer tokens to user1
      await neuroCoin.transfer(user1.address, stakeAmount);
      
      // User1 stakes tokens
      await neuroCoin.connect(user1).stakeTokens(stakeAmount);
      
      // Fast forward time by 30 days
      await ethers.provider.send("evm_increaseTime", [30 * 24 * 60 * 60]);
      await ethers.provider.send("evm_mine");
      
      // Unstake tokens
      await neuroCoin.connect(user1).unstakeTokens(stakeAmount);
      
      expect(await neuroCoin.stakedBalances(user1.address)).to.equal(0);
      expect(await neuroCoin.balanceOf(user1.address)).to.equal(stakeAmount);
    });
    
    it("Should not allow unstaking before staking period", async function () {
      const { neuroCoin, owner, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      const stakeAmount = ethers.utils.parseEther("1000");
      
      // Transfer tokens to user1
      await neuroCoin.transfer(user1.address, stakeAmount);
      
      // User1 stakes tokens
      await neuroCoin.connect(user1).stakeTokens(stakeAmount);
      
      // Try to unstake immediately
      await expect(
        neuroCoin.connect(user1).unstakeTokens(stakeAmount)
      ).to.be.revertedWith("NRC: Staking period not completed");
    });
  });
  
  describe("Marketplace Functions", function () {
    it("Should allow authorized marketplace to transfer with fees", async function () {
      const { neuroCoin, owner, feeCollector, user1, user2, marketplace } = await loadFixture(deployNeuroCoinFixture);
      
      // Authorize marketplace
      await neuroCoin.setMarketplaceAuthorization(marketplace.address, true);
      
      const transferAmount = ethers.utils.parseEther("1000");
      const feeRate = await neuroCoin.transactionFeeRate();
      const expectedFee = transferAmount.mul(feeRate).div(10000);
      const expectedTransfer = transferAmount.sub(expectedFee);
      
      // Transfer tokens to user1
      await neuroCoin.transfer(user1.address, transferAmount);
      
      // Marketplace transfer
      await neuroCoin.connect(marketplace).marketplaceTransfer(
        user1.address,
        user2.address,
        transferAmount
      );
      
      expect(await neuroCoin.balanceOf(user2.address)).to.equal(expectedTransfer);
      expect(await neuroCoin.balanceOf(feeCollector.address)).to.equal(expectedFee);
    });
    
    it("Should not allow unauthorized marketplace transfer", async function () {
      const { neuroCoin, user1, user2 } = await loadFixture(deployNeuroCoinFixture);
      
      const transferAmount = ethers.utils.parseEther("1000");
      
      await expect(
        neuroCoin.connect(user1).marketplaceTransfer(
          user1.address,
          user2.address,
          transferAmount
        )
      ).to.be.revertedWith("NRC: Not authorized marketplace");
    });
  });
  
  describe("Batch Transfer", function () {
    it("Should allow batch transfers", async function () {
      const { neuroCoin, owner, user1, user2 } = await loadFixture(deployNeuroCoinFixture);
      
      const transferAmount = ethers.utils.parseEther("500");
      const recipients = [user1.address, user2.address];
      const amounts = [transferAmount, transferAmount];
      
      await neuroCoin.batchTransfer(recipients, amounts);
      
      expect(await neuroCoin.balanceOf(user1.address)).to.equal(transferAmount);
      expect(await neuroCoin.balanceOf(user2.address)).to.equal(transferAmount);
    });
    
    it("Should not allow batch transfer with mismatched arrays", async function () {
      const { neuroCoin, owner, user1, user2 } = await loadFixture(deployNeuroCoinFixture);
      
      const transferAmount = ethers.utils.parseEther("500");
      const recipients = [user1.address, user2.address];
      const amounts = [transferAmount]; // Mismatched length
      
      await expect(
        neuroCoin.batchTransfer(recipients, amounts)
      ).to.be.revertedWith("NRC: Arrays length mismatch");
    });
  });
  
  describe("Pausable", function () {
    it("Should allow owner to pause and unpause", async function () {
      const { neuroCoin, owner, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      // Pause the contract
      await neuroCoin.pause();
      expect(await neuroCoin.paused()).to.be.true;
      
      // Try to transfer while paused
      await expect(
        neuroCoin.transfer(user1.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Pausable: paused");
      
      // Unpause the contract
      await neuroCoin.unpause();
      expect(await neuroCoin.paused()).to.be.false;
      
      // Transfer should work now
      await neuroCoin.transfer(user1.address, ethers.utils.parseEther("100"));
      expect(await neuroCoin.balanceOf(user1.address)).to.equal(ethers.utils.parseEther("100"));
    });
    
    it("Should not allow non-owner to pause", async function () {
      const { neuroCoin, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      await expect(
        neuroCoin.connect(user1).pause()
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });
  
  describe("Fee Management", function () {
    it("Should allow owner to update transaction fee rate", async function () {
      const { neuroCoin, owner } = await loadFixture(deployNeuroCoinFixture);
      
      const newFeeRate = 100; // 1%
      await neuroCoin.setTransactionFeeRate(newFeeRate);
      
      expect(await neuroCoin.transactionFeeRate()).to.equal(newFeeRate);
    });
    
    it("Should not allow fee rate above maximum", async function () {
      const { neuroCoin, owner } = await loadFixture(deployNeuroCoinFixture);
      
      const maxFeeRate = await neuroCoin.MAX_FEE_RATE();
      const excessiveFeeRate = maxFeeRate.add(1);
      
      await expect(
        neuroCoin.setTransactionFeeRate(excessiveFeeRate)
      ).to.be.revertedWith("NRC: Fee rate too high");
    });
    
    it("Should allow owner to update fee collector", async function () {
      const { neuroCoin, owner, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      await neuroCoin.setFeeCollector(user1.address);
      expect(await neuroCoin.feeCollector()).to.equal(user1.address);
    });
  });
  
  describe("User Info", function () {
    it("Should return comprehensive user information", async function () {
      const { neuroCoin, owner, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      const transferAmount = ethers.utils.parseEther("1000");
      const stakeAmount = ethers.utils.parseEther("500");
      
      // Transfer tokens to user1
      await neuroCoin.transfer(user1.address, transferAmount);
      
      // User1 stakes some tokens
      await neuroCoin.connect(user1).stakeTokens(stakeAmount);
      
      const userInfo = await neuroCoin.getUserInfo(user1.address);
      
      expect(userInfo.balance).to.equal(transferAmount.sub(stakeAmount));
      expect(userInfo.stakedBalance).to.equal(stakeAmount);
      expect(userInfo.totalRewardsClaimed).to.equal(0);
    });
  });
  
  describe("Events", function () {
    it("Should emit TokensStaked event", async function () {
      const { neuroCoin, owner, user1 } = await loadFixture(deployNeuroCoinFixture);
      
      const stakeAmount = ethers.utils.parseEther("1000");
      await neuroCoin.transfer(user1.address, stakeAmount);
      
      await expect(neuroCoin.connect(user1).stakeTokens(stakeAmount))
        .to.emit(neuroCoin, "TokensStaked")
        .withArgs(user1.address, stakeAmount);
    });
    
    it("Should emit MarketplaceAuthorized event", async function () {
      const { neuroCoin, marketplace } = await loadFixture(deployNeuroCoinFixture);
      
      await expect(neuroCoin.setMarketplaceAuthorization(marketplace.address, true))
        .to.emit(neuroCoin, "MarketplaceAuthorized")
        .withArgs(marketplace.address, true);
    });
    
    it("Should emit FeeRateUpdated event", async function () {
      const { neuroCoin } = await loadFixture(deployNeuroCoinFixture);
      
      const oldRate = await neuroCoin.transactionFeeRate();
      const newRate = 100;
      
      await expect(neuroCoin.setTransactionFeeRate(newRate))
        .to.emit(neuroCoin, "FeeRateUpdated")
        .withArgs(oldRate, newRate);
    });
  });
});

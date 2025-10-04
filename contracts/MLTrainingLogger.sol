// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title MLTrainingLogger
 * @dev Smart contract for logging ML training jobs on the blockchain
 */
contract MLTrainingLogger is Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;
    
    Counters.Counter private _trainingJobIds;
    
    struct TrainingJob {
        uint256 id;
        address trainer;
        string jobId; // Backend job ID
        string datasetHash; // IPFS hash of the dataset
        string algorithmName;
        string algorithmType; // classification, regression, clustering, etc.
        uint256 startTime;
        uint256 endTime;
        bool isCompleted;
        string modelHash; // IPFS hash of the trained model
        string metricsHash; // IPFS hash of the training metrics
        uint256 cost; // Cost in wei
        uint8 status; // 0: created, 1: running, 2: completed, 3: failed, 4: cancelled
    }
    
    struct TrainingMetrics {
        uint256 accuracy; // Scaled by 10000 (e.g., 8500 = 85.00%)
        uint256 precision; // Scaled by 10000
        uint256 recall; // Scaled by 10000
        uint256 f1Score; // Scaled by 10000
        uint256 trainingTime; // In seconds
        uint256 memoryUsed; // In MB
        string additionalMetrics; // JSON string for other metrics
    }
    
    // Mappings
    mapping(uint256 => TrainingJob) public trainingJobs;
    mapping(uint256 => TrainingMetrics) public trainingMetrics;
    mapping(address => uint256[]) public userTrainingJobs;
    mapping(string => uint256) public jobIdToBlockchainId; // Backend job ID to blockchain ID
    
    // Events
    event TrainingJobCreated(
        uint256 indexed jobId,
        address indexed trainer,
        string backendJobId,
        string datasetHash,
        string algorithmName,
        string algorithmType
    );
    
    event TrainingJobStarted(
        uint256 indexed jobId,
        address indexed trainer,
        uint256 startTime
    );
    
    event TrainingJobCompleted(
        uint256 indexed jobId,
        address indexed trainer,
        uint256 endTime,
        string modelHash,
        string metricsHash
    );
    
    event TrainingJobFailed(
        uint256 indexed jobId,
        address indexed trainer,
        uint256 endTime,
        string reason
    );
    
    event TrainingJobCancelled(
        uint256 indexed jobId,
        address indexed trainer,
        uint256 cancelTime
    );
    
    event MetricsRecorded(
        uint256 indexed jobId,
        uint256 accuracy,
        uint256 precision,
        uint256 recall,
        uint256 f1Score
    );
    
    /**
     * @dev Create a new training job log
     */
    function createTrainingJob(
        string memory _backendJobId,
        string memory _datasetHash,
        string memory _algorithmName,
        string memory _algorithmType,
        uint256 _estimatedCost
    ) external returns (uint256) {
        _trainingJobIds.increment();
        uint256 newJobId = _trainingJobIds.current();
        
        TrainingJob storage job = trainingJobs[newJobId];
        job.id = newJobId;
        job.trainer = msg.sender;
        job.jobId = _backendJobId;
        job.datasetHash = _datasetHash;
        job.algorithmName = _algorithmName;
        job.algorithmType = _algorithmType;
        job.startTime = 0; // Will be set when training starts
        job.endTime = 0;
        job.isCompleted = false;
        job.cost = _estimatedCost;
        job.status = 0; // created
        
        userTrainingJobs[msg.sender].push(newJobId);
        jobIdToBlockchainId[_backendJobId] = newJobId;
        
        emit TrainingJobCreated(
            newJobId,
            msg.sender,
            _backendJobId,
            _datasetHash,
            _algorithmName,
            _algorithmType
        );
        
        return newJobId;
    }
    
    /**
     * @dev Start a training job
     */
    function startTrainingJob(string memory _backendJobId) external {
        uint256 jobId = jobIdToBlockchainId[_backendJobId];
        require(jobId > 0, "Training job not found");
        
        TrainingJob storage job = trainingJobs[jobId];
        require(job.trainer == msg.sender, "Not authorized");
        require(job.status == 0, "Job already started");
        
        job.startTime = block.timestamp;
        job.status = 1; // running
        
        emit TrainingJobStarted(jobId, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Complete a training job with results
     */
    function completeTrainingJob(
        string memory _backendJobId,
        string memory _modelHash,
        string memory _metricsHash,
        uint256 _actualCost
    ) external {
        uint256 jobId = jobIdToBlockchainId[_backendJobId];
        require(jobId > 0, "Training job not found");
        
        TrainingJob storage job = trainingJobs[jobId];
        require(job.trainer == msg.sender, "Not authorized");
        require(job.status == 1, "Job not running");
        
        job.endTime = block.timestamp;
        job.isCompleted = true;
        job.modelHash = _modelHash;
        job.metricsHash = _metricsHash;
        job.cost = _actualCost;
        job.status = 2; // completed
        
        emit TrainingJobCompleted(
            jobId,
            msg.sender,
            block.timestamp,
            _modelHash,
            _metricsHash
        );
    }
    
    /**
     * @dev Record training metrics
     */
    function recordMetrics(
        string memory _backendJobId,
        uint256 _accuracy,
        uint256 _precision,
        uint256 _recall,
        uint256 _f1Score,
        uint256 _trainingTime,
        uint256 _memoryUsed,
        string memory _additionalMetrics
    ) external {
        uint256 jobId = jobIdToBlockchainId[_backendJobId];
        require(jobId > 0, "Training job not found");
        
        TrainingJob storage job = trainingJobs[jobId];
        require(job.trainer == msg.sender, "Not authorized");
        
        TrainingMetrics storage metrics = trainingMetrics[jobId];
        metrics.accuracy = _accuracy;
        metrics.precision = _precision;
        metrics.recall = _recall;
        metrics.f1Score = _f1Score;
        metrics.trainingTime = _trainingTime;
        metrics.memoryUsed = _memoryUsed;
        metrics.additionalMetrics = _additionalMetrics;
        
        emit MetricsRecorded(
            jobId,
            _accuracy,
            _precision,
            _recall,
            _f1Score
        );
    }
    
    /**
     * @dev Fail a training job
     */
    function failTrainingJob(
        string memory _backendJobId,
        string memory _reason
    ) external {
        uint256 jobId = jobIdToBlockchainId[_backendJobId];
        require(jobId > 0, "Training job not found");
        
        TrainingJob storage job = trainingJobs[jobId];
        require(job.trainer == msg.sender, "Not authorized");
        require(job.status == 1, "Job not running");
        
        job.endTime = block.timestamp;
        job.status = 3; // failed
        
        emit TrainingJobFailed(jobId, msg.sender, block.timestamp, _reason);
    }
    
    /**
     * @dev Cancel a training job
     */
    function cancelTrainingJob(string memory _backendJobId) external {
        uint256 jobId = jobIdToBlockchainId[_backendJobId];
        require(jobId > 0, "Training job not found");
        
        TrainingJob storage job = trainingJobs[jobId];
        require(job.trainer == msg.sender, "Not authorized");
        require(job.status <= 1, "Job already completed or failed");
        
        job.endTime = block.timestamp;
        job.status = 4; // cancelled
        
        emit TrainingJobCancelled(jobId, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Get training job details
     */
    function getTrainingJob(uint256 _jobId) external view returns (
        uint256 id,
        address trainer,
        string memory jobId,
        string memory datasetHash,
        string memory algorithmName,
        string memory algorithmType,
        uint256 startTime,
        uint256 endTime,
        bool isCompleted,
        string memory modelHash,
        string memory metricsHash,
        uint256 cost,
        uint8 status
    ) {
        TrainingJob storage job = trainingJobs[_jobId];
        return (
            job.id,
            job.trainer,
            job.jobId,
            job.datasetHash,
            job.algorithmName,
            job.algorithmType,
            job.startTime,
            job.endTime,
            job.isCompleted,
            job.modelHash,
            job.metricsHash,
            job.cost,
            job.status
        );
    }
    
    /**
     * @dev Get training metrics
     */
    function getTrainingMetrics(uint256 _jobId) external view returns (
        uint256 accuracy,
        uint256 precision,
        uint256 recall,
        uint256 f1Score,
        uint256 trainingTime,
        uint256 memoryUsed,
        string memory additionalMetrics
    ) {
        TrainingMetrics storage metrics = trainingMetrics[_jobId];
        return (
            metrics.accuracy,
            metrics.precision,
            metrics.recall,
            metrics.f1Score,
            metrics.trainingTime,
            metrics.memoryUsed,
            metrics.additionalMetrics
        );
    }
    
    /**
     * @dev Get user's training jobs
     */
    function getUserTrainingJobs(address _user) external view returns (uint256[] memory) {
        return userTrainingJobs[_user];
    }
    
    /**
     * @dev Get total number of training jobs
     */
    function getTotalTrainingJobs() external view returns (uint256) {
        return _trainingJobIds.current();
    }
    
    /**
     * @dev Get training job by backend job ID
     */
    function getTrainingJobByBackendId(string memory _backendJobId) external view returns (uint256) {
        return jobIdToBlockchainId[_backendJobId];
    }
    
    /**
     * @dev Get training statistics for a user
     */
    function getUserTrainingStats(address _user) external view returns (
        uint256 totalJobs,
        uint256 completedJobs,
        uint256 failedJobs,
        uint256 totalCost,
        uint256 totalTrainingTime
    ) {
        uint256[] memory userJobs = userTrainingJobs[_user];
        uint256 completed = 0;
        uint256 failed = 0;
        uint256 cost = 0;
        uint256 trainingTime = 0;
        
        for (uint256 i = 0; i < userJobs.length; i++) {
            TrainingJob storage job = trainingJobs[userJobs[i]];
            if (job.status == 2) { // completed
                completed++;
                cost += job.cost;
                trainingTime += trainingMetrics[userJobs[i]].trainingTime;
            } else if (job.status == 3) { // failed
                failed++;
            }
        }
        
        return (userJobs.length, completed, failed, cost, trainingTime);
    }
}

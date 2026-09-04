// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title FaceMatchRegistry
/// @notice Stores tamper-evident records of face-match results on-chain.
///         Each record stores image/embedding hashes and the reverse-image-search
///         match URL.  Anyone can verify a record's integrity by recomputing the
///         hashes off-chain and comparing.
contract FaceMatchRegistry {
    struct Record {
        uint256 id;
        bytes32 imageHash;
        bytes32 embeddingHash;
        string  matchUrl;
        string  matchSource;
        uint256 timestamp;
        address reporter;
    }

    uint256 public nextId;
    mapping(uint256 => Record) public records;

    event MatchRecorded(
        uint256 indexed id,
        bytes32 indexed imageHash,
        bytes32 indexed embeddingHash,
        string  matchUrl,
        string  matchSource,
        uint256 timestamp,
        address reporter
    );

    /// @notice Store a new face-match record. Returns the record id.
    function recordMatch(
        bytes32 _imageHash,
        bytes32 _embeddingHash,
        string calldata _matchUrl,
        string calldata _matchSource
    ) external returns (uint256) {
        uint256 id = nextId++;
        records[id] = Record(
            id,
            _imageHash,
            _embeddingHash,
            _matchUrl,
            _matchSource,
            block.timestamp,
            msg.sender
        );
        emit MatchRecorded(
            id,
            _imageHash,
            _embeddingHash,
            _matchUrl,
            _matchSource,
            block.timestamp,
            msg.sender
        );
        return id;
    }

    /// @notice Read back a record by id.
    function getRecord(uint256 _id)
        external
        view
        returns (
            bytes32 imageHash,
            bytes32 embeddingHash,
            string memory matchUrl,
            string memory matchSource,
            uint256 timestamp,
            address reporter
        )
    {
        Record storage r = records[_id];
        return (
            r.imageHash,
            r.embeddingHash,
            r.matchUrl,
            r.matchSource,
            r.timestamp,
            r.reporter
        );
    }
}

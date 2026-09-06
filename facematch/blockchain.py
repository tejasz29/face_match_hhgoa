"""Blockchain recording and verification on Polygon Amoy testnet.

Uses the FaceMatchRegistry smart contract to store a tamper-evident record
of each face-match pipeline run, and can read it back to verify integrity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from web3 import Web3
from web3._utils.events import EventLogErrorFlags

from facematch import config, ui

# Minimal ABI — just what we need for recordMatch + getRecord
_CONTRACT_ABI = [
    {
        "inputs": [
            {"name": "_imageHash", "type": "bytes32"},
            {"name": "_embeddingHash", "type": "bytes32"},
            {"name": "_matchUrl", "type": "string"},
            {"name": "_matchSource", "type": "string"},
        ],
        "name": "recordMatch",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "_id", "type": "uint256"}],
        "name": "getRecord",
        "outputs": [
            {"name": "imageHash", "type": "bytes32"},
            {"name": "embeddingHash", "type": "bytes32"},
            {"name": "matchUrl", "type": "string"},
            {"name": "matchSource", "type": "string"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "reporter", "type": "address"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "id", "type": "uint256"},
            {"indexed": True, "name": "imageHash", "type": "bytes32"},
            {"indexed": True, "name": "embeddingHash", "type": "bytes32"},
            {"indexed": False, "name": "matchUrl", "type": "string"},
            {"indexed": False, "name": "matchSource", "type": "string"},
            {"indexed": False, "name": "timestamp", "type": "uint256"},
            {"indexed": False, "name": "reporter", "type": "address"},
        ],
        "name": "MatchRecorded",
        "type": "event",
    },
]


@dataclass
class OnChainRecord:
    record_id: int
    image_hash: str
    embedding_hash: str
    match_url: str
    match_source: str
    timestamp: int
    reporter: str


def _get_w3() -> Web3:
    return Web3(Web3.HTTPProvider(config.RPC_URL))


def _get_contract(w3: Optional[Web3] = None):
    if w3 is None:
        w3 = _get_w3()
    if not config.CONTRACT_ADDRESS:
        raise ValueError(
            "CONTRACT_ADDRESS not set. Deploy the contract first:\n"
            "    python scripts/deploy_contract.py"
        )
    return w3.eth.contract(
        address=Web3.to_checksum_address(config.CONTRACT_ADDRESS),
        abi=_CONTRACT_ABI,
    )


def record_match(
    image_sha256: str,
    embedding_sha256: str,
    match_url: str,
    match_source: str,
) -> tuple[str, int]:
    """Write a face-match record to the blockchain.

    Returns ``(tx_hash_hex, record_id)``.
    """
    if not config.PRIVATE_KEY:
        raise ValueError("PRIVATE_KEY not set in .env")

    w3 = _get_w3()
    contract = _get_contract(w3)
    account = w3.eth.account.from_key(config.PRIVATE_KEY)

    # Pad hex hashes to bytes32
    image_hash = bytes.fromhex(image_sha256)
    embedding_hash = bytes.fromhex(embedding_sha256)

    ui.bullet(f"Sending transaction from {account.address} ...")
    tx = contract.functions.recordMatch(
        image_hash,
        embedding_hash,
        match_url,
        match_source,
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": config.CHAIN_ID,
        "gas": 500_000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    ui.info(f"Transaction hash : {ui.short(tx_hash.hex())}")
    ui.info(f"Explorer link    : {config.explorer_tx(tx_hash.hex())}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    ui.ok(f"Confirmed on-chain in block {receipt.blockNumber}")

    # Extract record id from event logs.
    # Ignore unrelated logs emitted alongside ours (e.g. ERC-20 transfers) so
    # web3 doesn't warn with MismatchedABI when decoding them against our ABI.
    events = contract.events.MatchRecorded().process_receipt(
        receipt, errors=EventLogErrorFlags.Ignore
    )
    record_id = events[0]["args"]["id"]
    ui.ok(f"Record written on-chain  (record ID: {record_id})")

    return tx_hash.hex(), record_id


def read_record(record_id: int) -> OnChainRecord:
    """Read a record back from the blockchain."""
    w3 = _get_w3()
    contract = _get_contract(w3)

    result = contract.functions.getRecord(record_id).call()
    image_hash, embedding_hash, match_url, match_source, timestamp, reporter = result

    return OnChainRecord(
        record_id=record_id,
        image_hash=image_hash.hex(),
        embedding_hash=embedding_hash.hex(),
        match_url=match_url,
        match_source=match_source,
        timestamp=timestamp,
        reporter=reporter,
    )


def verify_record(
    record_id: int,
    expected_image_sha256: str,
    expected_embedding_sha256: str,
) -> bool:
    """Read the record and confirm hashes match local values.

    Returns ``True`` if the on-chain record is tamper-evident-consistent.
    """
    rec = read_record(record_id)
    img_ok = rec.image_hash == expected_image_sha256
    emb_ok = rec.embedding_hash == expected_embedding_sha256

    print(f"[verify] Record #{rec.record_id}:")
    print(f"  image_hash:     {rec.image_hash}")
    print(f"  expected:       {expected_image_sha256}")
    print(f"  image match:    {'YES' if img_ok else 'NO — MISMATCH!'}")
    print(f"  embedding_hash: {rec.embedding_hash}")
    print(f"  expected:       {expected_embedding_sha256}")
    print(f"  embedding match:{'YES' if emb_ok else 'NO — MISMATCH!'}")
    print(f"  match_url:      {rec.match_url}")
    print(f"  timestamp:      {rec.timestamp}")
    print(f"  reporter:       {rec.reporter}")

    return img_ok and emb_ok

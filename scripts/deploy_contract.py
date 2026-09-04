"""CLI: compile and deploy FaceMatchRegistry to Polygon Amoy testnet.

Usage:
    python scripts/deploy_contract.py

Requires a funded wallet — see scripts/new_wallet.py and .env configuration.
Saves the deployed contract address to .env and deployment.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from solcx import compile_standard, install_solc
from web3 import Web3

from facematch import config

SOLC_VERSION = "0.8.28"
CONTRACT_SOURCE = (Path(__file__).resolve().parent.parent / "contracts" / "FaceMatchRegistry.sol").read_text()


def deploy() -> str:
    """Compile, deploy, and return the contract address."""
    if not config.PRIVATE_KEY:
        raise ValueError("PRIVATE_KEY not set in .env")

    # Install compiler
    print(f"[deploy] Installing solc {SOLC_VERSION} ...")
    install_solc(SOLC_VERSION)

    # Compile
    print("[deploy] Compiling FaceMatchRegistry ...")
    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {"FaceMatchRegistry.sol": {"content": CONTRACT_SOURCE}},
            "settings": {
                "outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}},
                "optimizer": {"enabled": True, "runs": 200},
            },
        },
        solc_version=SOLC_VERSION,
    )

    contract_data = compiled["contracts"]["FaceMatchRegistry.sol"]["FaceMatchRegistry"]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]

    # Connect
    w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
    chain_id = config.CHAIN_ID
    account = w3.eth.account.from_key(config.PRIVATE_KEY)

    print(f"[deploy] Deploying from {account.address} on chain {chain_id} ...")

    Contract = w3.eth.contract(abi=abi, bytecode=bytes.fromhex(bytecode))
    tx = Contract.constructor().build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": chain_id,
        "gas": 3_000_000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"[deploy] TX sent: {tx_hash.hex()}")
    print(f"[deploy] Explorer: {config.explorer_tx(tx_hash.hex())}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    contract_address = receipt.contractAddress
    print(f"[deploy] Contract deployed at: {contract_address}")
    print(f"[deploy] Explorer: {config.explorer_address(contract_address)}")

    # Save to .env
    env_path = config.ROOT / ".env"
    if env_path.exists():
        content = env_path.read_text()
        if "CONTRACT_ADDRESS=" in content:
            content = re.sub(r"CONTRACT_ADDRESS=.*", f"CONTRACT_ADDRESS={contract_address}", content)
        else:
            content += f"\nCONTRACT_ADDRESS={contract_address}\n"
        env_path.write_text(content)
    else:
        env_path.write_text(f"CONTRACT_ADDRESS={contract_address}\n")
    print(f"[deploy] Saved CONTRACT_ADDRESS to .env")

    # Save deployment metadata
    deploy_meta = {
        "chain": "Polygon Amoy",
        "chain_id": chain_id,
        "contract_address": contract_address,
        "deployer": account.address,
        "tx_hash": tx_hash.hex(),
        "explorer": config.explorer_tx(tx_hash.hex()),
        "solc_version": SOLC_VERSION,
    }
    deploy_path = config.ROOT / "deployment.json"
    deploy_path.write_text(json.dumps(deploy_meta, indent=2) + "\n")
    print(f"[deploy] Saved deployment metadata to deployment.json")

    return contract_address


if __name__ == "__main__":
    deploy()

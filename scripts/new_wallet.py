"""CLI: generate a throwaway Polygon Amoy testnet wallet.

Usage:
    python scripts/new_wallet.py

Prints the address and private key.  Paste the private key into your .env.
NEVER use this key on mainnet — it is generated from a weak entropy source
and is meant for testnet experimentation only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eth_account import Account


def main() -> None:
    acct = Account.create()
    print("=" * 60)
    print("  Throwaway Amoy testnet wallet generated")
    print("=" * 60)
    print(f"  Address:     {acct.address}")
    print(f"  Private key: {acct.key.hex()}")
    print()
    print("Fund this address from the Polygon Amoy faucet:")
    print("  https://faucet.polygon.technology")
    print()
    print("Then paste the PRIVATE KEY into your .env file.")
    print("=" * 60)


if __name__ == "__main__":
    main()

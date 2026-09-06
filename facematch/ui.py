"""Friendly console output for the pipeline.

Keeps the terminal legible for a screen recording: each stage is a
numbered step with plain-language lines.
"""
from __future__ import annotations

BAR = "─" * 88
WIDE_BAR = "═" * 88

VERBOSE = False
_warnings = 0


def set_verbose(flag: bool) -> None:
    global VERBOSE
    VERBOSE = bool(flag)


def header(title: str) -> None:
    print()
    print(WIDE_BAR)
    print(f"    {title}")
    print(WIDE_BAR)


def step(number: int, total: int, title: str) -> None:
    print()
    print(BAR)
    print(f"  STEP {number} OF {total}  \u00b7  {title}")
    print(BAR)


def ok(msg: str) -> None:
    print(f"  \u2713 {msg}")


def info(msg: str) -> None:
    print(f"    {msg}")


def bullet(msg: str) -> None:
    print(f"  \u00b7 {msg}")


def warn(msg: str) -> None:
    global _warnings
    _warnings += 1
    print(f"  \u26a0 {msg}")


def short(value: str, head: int = 12, tail: int = 4) -> str:
    """Truncate a long hash/url for readable lines."""
    if len(value) <= head + tail + 1:
        return value
    return f"{value[:head]}\u2026{value[-tail:]}"


def hashes_block(
    image_sha256: str,
    embedding_sha256: str,
) -> None:
    """Show image + face fingerprints (short, or full in verbose)."""
    ok(f"Image fingerprint (SHA-256): {image_sha256 if VERBOSE else short(image_sha256)}")
    ok(f"Face  fingerprint (SHA-256): {embedding_sha256 if VERBOSE else short(embedding_sha256)}")


def divider(text: str | None = None) -> None:
    print(BAR)
    if text:
        print(f"  {text}")
        print(BAR)


def blank() -> None:
    print()
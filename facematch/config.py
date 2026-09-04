"""Central configuration: paths, model URLs, chain constants, env loading.

All secrets come from a local ``.env`` file (see ``.env.example``). Importing this
module never fails if ``python-dotenv`` is missing or ``.env`` is absent — env-backed
values simply fall back to defaults / empty strings.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
OUTPUT_DIR = ROOT / "output"
SAMPLES_DIR = ROOT / "samples"


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


_load_env()

# --- Face models (OpenCV Zoo) ------------------------------------------------
YUNET_FILENAME = "face_detection_yunet_2023mar.onnx"
SFACE_FILENAME = "face_recognition_sface_2021dec.onnx"
YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/"
    "models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
SFACE_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/"
    "models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
)
YUNET_PATH = MODELS_DIR / YUNET_FILENAME
SFACE_PATH = MODELS_DIR / SFACE_FILENAME

# Detection tuning
DET_SCORE_THRESHOLD = 0.85
DET_NMS_THRESHOLD = 0.30
DET_TOP_K = 5000

# --- SerpAPI (reverse image search) ------------------------------------------
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
SERPAPI_ENDPOINT = "https://serpapi.com/search"

# Domains we count as a "social media post".
SOCIAL_DOMAINS = [
    "instagram.com", "twitter.com", "x.com", "facebook.com", "fb.com",
    "linkedin.com", "tiktok.com", "youtube.com", "youtu.be", "threads.net",
    "reddit.com", "pinterest.com", "pin.it", "tumblr.com", "snapchat.com",
    "weibo.com", "vk.com", "flickr.com", "mastodon.social", "bsky.app",
]

# --- Blockchain: Polygon Amoy testnet ---------------------------------------
RPC_URL = os.getenv("RPC_URL", "https://polygon-amoy-bor-rpc.publicnode.com")
CHAIN_ID = int(os.getenv("CHAIN_ID", "80002"))
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")
EXPLORER_BASE = os.getenv("EXPLORER_BASE", "https://amoy.polygonscan.com").rstrip("/")


def explorer_tx(tx_hash: str) -> str:
    return f"{EXPLORER_BASE}/tx/{tx_hash}"


def explorer_address(addr: str) -> str:
    return f"{EXPLORER_BASE}/address/{addr}"

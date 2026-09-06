"""Download + cache the OpenCV Zoo ONNX models used for face detection/encoding."""
from __future__ import annotations

import urllib.request
from pathlib import Path

from facematch import config, ui


def _download(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return False
    ui.info(f"Downloading {dest.name} (first run only) ...")
    req = urllib.request.Request(url, headers={"User-Agent": "face-match/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return True


def ensure_models() -> tuple[Path, Path]:
    """Ensure both ONNX models exist locally; download any that are missing."""
    _download(config.YUNET_URL, config.YUNET_PATH)
    _download(config.SFACE_URL, config.SFACE_PATH)
    ui.ok("Face AI models ready")
    return config.YUNET_PATH, config.SFACE_PATH

"""Download + cache the OpenCV Zoo ONNX models used for face detection/encoding."""
from __future__ import annotations

import urllib.request
from pathlib import Path

from facematch import config


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[skip] {dest.name} already present ({dest.stat().st_size:,} bytes)")
        return
    print(f"[download] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "face-match/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    dest.write_bytes(data)
    print(f"[ok] {dest.name} ({dest.stat().st_size:,} bytes)")


def ensure_models() -> tuple[Path, Path]:
    """Ensure both ONNX models exist locally; download any that are missing."""
    _download(config.YUNET_URL, config.YUNET_PATH)
    _download(config.SFACE_URL, config.SFACE_PATH)
    return config.YUNET_PATH, config.SFACE_PATH

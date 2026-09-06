"""Upload a local image to a temporary public host to get a URL.

SerpAPI's Google Lens endpoint requires a publicly accessible image URL.
This module tries a chain of free, no-auth-required hosts:

  1. catbox.moe   (anonymous upload, 200 MB limit, lasts ~1 hour)
  2. 0x0.st        (anonymous upload, 512 MB limit, auto-expires)
  3. tmpfiles.org  (anonymous upload, 100 MB limit, 60 min TTL)

If the input is already a URL, it is returned as-is.
"""
from __future__ import annotations

import mimetypes
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

from facematch import ui

# ---------------------------------------------------------------------------
# Host backends
# ---------------------------------------------------------------------------

def _upload_catbox(data: bytes, filename: str, content_type: str) -> Optional[str]:
    """Upload to catbox.moe anonymous endpoint."""
    url = "https://catbox.moe/user/api.php"
    try:
        resp = requests.post(
            url,
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (filename, data, content_type)},
            timeout=60,
        )
        if resp.status_code == 200 and resp.text.startswith("http"):
            return resp.text.strip()
    except Exception:
        pass
    return None


def _upload_0x0(data: bytes, filename: str, content_type: str) -> Optional[str]:
    """Upload to 0x0.st anonymous endpoint."""
    url = "https://0x0.st"
    try:
        resp = requests.post(
            url,
            files={"file": (filename, data, content_type)},
            timeout=60,
        )
        if resp.status_code == 200 and resp.text.startswith("http"):
            return resp.text.strip()
    except Exception:
        pass
    return None


def _upload_tmpfiles(data: bytes, filename: str, content_type: str) -> Optional[str]:
    """Upload to tmpfiles.org anonymous endpoint."""
    url = "https://tmpfiles.org/api/v1/upload"
    try:
        resp = requests.post(
            url,
            files={"file": (filename, data, content_type)},
            timeout=60,
        )
        if resp.status_code == 200:
            body = resp.json()
            if body.get("status") == "success":
                # tmpfiles.org returns a viewer URL; convert to direct link
                link = body["data"]["url"]
                return link.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception:
        pass
    return None


UPLOAD_CHAIN = [
    ("catbox.moe", _upload_catbox),
    ("0x0.st", _upload_0x0),
    ("tmpfiles.org", _upload_tmpfiles),
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_url(source: str) -> bool:
    """Return True if *source* looks like an HTTP(S) URL."""
    parsed = urlparse(source)
    return parsed.scheme in ("http", "https")


def host_image(
    source: str,
    *,
    raw_bytes: Optional[bytes] = None,
) -> str:
    """Return a publicly accessible URL for *source*.

    If *source* is already a URL it is returned unchanged.
    Otherwise the image bytes are uploaded to a temporary host.
    """
    if is_url(source):
        return source

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {source}")

    data = raw_bytes or path.read_bytes()
    content_type = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    filename = path.name

    for host_name, uploader in UPLOAD_CHAIN:
        ui.bullet(f"Uploading image to a public host ({host_name}) ...")
        public_url = uploader(data, filename, content_type)
        if public_url:
            ui.ok(f"Image is now live at: {public_url}")
            return public_url

    raise RuntimeError(
        "All temporary image hosts failed. "
        "Provide a public --image-url instead."
    )

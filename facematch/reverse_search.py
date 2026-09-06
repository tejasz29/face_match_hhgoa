"""Reverse image search via SerpAPI Google Lens.

Returns the best matching social-media post (or top overall match as fallback).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import requests

from facematch import config, ui


@dataclass
class SearchResult:
    title: str
    url: str
    source: str
    domain: str
    thumbnail: str
    is_social: bool


def _extract_domain(url: str) -> str:
    """Return the lowercase registered domain (e.g. 'instagram.com')."""
    host = urlparse(url).hostname or ""
    parts = host.lower().split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host.lower()


def _is_social_domain(domain: str) -> bool:
    for sd in config.SOCIAL_DOMAINS:
        if domain == sd or domain.endswith("." + sd):
            return True
    return False


def search(
    image_url: str,
    *,
    api_key: Optional[str] = None,
) -> Optional[SearchResult]:
    """Run a Google Lens reverse-image search and return the best match.

    Returns ``None`` if SerpAPI returns no visual matches at all.
    """
    key = api_key or config.SERPAPI_KEY
    if not key:
        raise ValueError(
            "SERPAPI_KEY is not set. "
            "Add it to your .env file (see .env.example)."
        )

    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": key,
    }

    ui.bullet("Searching the web (Google Lens) ...")
    resp = requests.get(config.SERPAPI_ENDPOINT, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    visual_matches = data.get("visual_matches", [])
    if not visual_matches:
        ui.bullet("No visual matches found.")
        return None

    ui.bullet(f"Found {len(visual_matches)} matching images on the web")

    # --- Pass 1: find the first social-media match ---
    for match in visual_matches:
        link = match.get("link", "")
        domain = _extract_domain(link)
        if _is_social_domain(domain):
            return SearchResult(
                title=match.get("title", ""),
                url=link,
                source=match.get("source", ""),
                domain=domain,
                thumbnail=match.get("thumbnail", ""),
                is_social=True,
            )

    # --- Pass 2: fallback to top overall match ---
    top = visual_matches[0]
    link = top.get("link", "")
    domain = _extract_domain(link)
    return SearchResult(
        title=top.get("title", ""),
        url=link,
        source=top.get("source", ""),
        domain=domain,
        thumbnail=top.get("thumbnail", ""),
        is_social=_is_social_domain(domain),
    )

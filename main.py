"""face_match — Face ID + Blockchain Verification pipeline.

Usage:
    python main.py --image <path>
    python main.py --image-url <public_url>
    python main.py --image <path> --verbose

Pipeline stages:
    1. Detect + encode face (OpenCV YuNet + SFace)
    2. Reverse-image search (SerpAPI Google Lens)
    3. Record match on Polygon Amoy testnet
    4. Read back and verify tamper-evidence
"""
from __future__ import annotations

import argparse
import json
import sys

from facematch import ui
from facematch.config import OUTPUT_DIR
from facematch.face_encoder import FaceEncoder, load_image_bgr
from facematch.image_host import host_image
from facematch.reverse_search import search
from facematch.blockchain import record_match, verify_record


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Face ID + Blockchain Verification pipeline"
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", type=str, help="Path to a local image file")
    group.add_argument("--image-url", type=str, help="Public URL of an image")
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Print full technical detail (complete hashes, raw values)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ui.set_verbose(args.verbose)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ui.header("FACE MATCH  \u00b7  BLOCKCHAIN VERIFICATION")

    if args.image_url:
        import requests
        resp = requests.get(args.image_url, timeout=30)
        resp.raise_for_status()
        raw_bytes = resp.content
        img, raw_bytes = load_image_bgr(raw_bytes=raw_bytes)
        source_label = args.image_url
    else:
        img, raw_bytes = load_image_bgr(source=args.image)
        source_label = args.image

    ui.info(f"Input image : {source_label}")
    ui.blank()

    # ── Stage 1: Face detection + encoding ─────────────────────────────
    ui.step(1, 4, "Detect the face")
    encoder = FaceEncoder()
    result = encoder.encode(img, raw_bytes)

    # Save aligned crop
    import cv2
    crop_path = OUTPUT_DIR / "face_crop.png"
    cv2.imwrite(str(crop_path), result.aligned_crop)

    ui.ok(f"Found {result.num_faces} face  \u00b7  confidence {result.score:.1%}")
    if args.verbose:
        ui.info(f"Raw confidence: {result.score}")
        ui.info(f"Bounding box: x={result.bbox[0]} y={result.bbox[1]} "
                f"w={result.bbox[2]} h={result.bbox[3]}")
    ui.ok("Created a unique face signature (128-d embedding)")
    ui.hashes_block(result.image_sha256, result.embedding_sha256)
    ui.ok(f"Saved the aligned face crop: {crop_path}")
    ui.blank()

    # ── Stage 2: Reverse image search ──────────────────────────────────
    ui.step(2, 4, "Search the web for this photo")
    if args.image_url:
        public_url = args.image_url
    else:
        public_url = host_image(source_label, raw_bytes=raw_bytes)

    search_result = search(public_url)
    if search_result is None:
        ui.warn("No matching post found online - recording the fingerprints only.")
        match_url = public_url
        match_source = "no_match"
    else:
        ui.ok(f"Found a matching post on {search_result.source}")
        ui.info(f"  Title : {search_result.title}")
        ui.info(f"  URL   : {search_result.url}")
        if search_result.is_social:
            ui.ok(f"Social media confirmed ({search_result.domain})")
        match_url = search_result.url
        match_source = search_result.source
    ui.blank()

    # ── Stage 3: Blockchain record ─────────────────────────────────────
    ui.step(3, 4, "Write the record to a blockchain")
    ui.info("Network: Polygon Amoy testnet")
    tx_hash, record_id = record_match(
        image_sha256=result.image_sha256,
        embedding_sha256=result.embedding_sha256,
        match_url=match_url,
        match_source=match_source,
    )
    ui.blank()

    # ── Stage 4: Verify ────────────────────────────────────────────────
    ui.step(4, 4, "Verify the record against the blockchain")
    ok = verify_record(
        record_id,
        expected_image_sha256=result.image_sha256,
        expected_embedding_sha256=result.embedding_sha256,
    )
    ui.blank()
    if ok:
        ui.ok("Record verified - on-chain data exactly matches this image. "
              "Tamper-evident.")
    else:
        ui.warn("MISMATCH detected - the on-chain record does not match!")
    ui.blank()

    # ── Save result JSON ───────────────────────────────────────────────
    output = {
        "source": source_label,
        "public_url": public_url,
        "face": {
            "bbox": list(result.bbox),
            "score": result.score,
            "num_faces": result.num_faces,
            "image_sha256": result.image_sha256,
            "embedding_sha256": result.embedding_sha256,
        },
        "search": {
            "match_url": match_url,
            "match_source": match_source,
            "is_social": search_result.is_social if search_result else False,
            "title": search_result.title if search_result else "",
        },
        "blockchain": {
            "chain": "Polygon Amoy",
            "tx_hash": tx_hash,
            "record_id": record_id,
            "explorer_tx": f"https://amoy.polygonscan.com/tx/{tx_hash}",
            "verified": ok,
        },
    }

    result_path = OUTPUT_DIR / "result.json"
    result_path.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Full result saved to: {result_path}")
    print("=" * 60)
    print("  Pipeline complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
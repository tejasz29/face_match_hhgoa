"""Face detection + encoding.

Uses OpenCV's built-in DNN face pipeline:
  * YuNet   (``cv2.FaceDetectorYN``)   -> detect + 5 landmarks
  * SFace   (``cv2.FaceRecognizerSF``) -> 128-d L2-normalized embedding

No heavyweight ML deps (dlib/tensorflow/torch) and no cloud keys — this runs
fully offline once the two small ONNX models are downloaded.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

from facematch import config
from facematch.models import ensure_models


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class FaceResult:
    bbox: tuple[int, int, int, int]   # x, y, w, h (pixels)
    score: float                      # detector confidence 0..1
    embedding: np.ndarray             # (128,) float32
    embedding_sha256: str             # sha256 of embedding.tobytes()
    image_sha256: str                 # sha256 of the source image bytes
    aligned_crop: np.ndarray          # aligned 112x112 BGR face crop
    num_faces: int                    # total faces detected in the image


def load_image_bgr(
    source: Union[str, Path, bytes, bytearray, None] = None,
    raw_bytes: Optional[bytes] = None,
) -> tuple[np.ndarray, bytes]:
    """Return ``(bgr_image, raw_bytes)``.

    ``source`` may be a filesystem path or raw bytes; alternatively pass
    ``raw_bytes`` directly (e.g. bytes downloaded from a URL).
    """
    if raw_bytes is None:
        if isinstance(source, (bytes, bytearray)):
            raw_bytes = bytes(source)
        else:
            raw_bytes = Path(source).read_bytes()
    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image (unsupported/corrupt format).")
    return img, raw_bytes


class FaceEncoder:
    """Loads the ONNX models once, then encodes faces on demand."""

    def __init__(self) -> None:
        from cv2.utils import logging as cv2_logging
        cv2_logging.setLogLevel(cv2_logging.LOG_LEVEL_ERROR)

        yunet_path, sface_path = ensure_models()
        self.detector = cv2.FaceDetectorYN.create(
            str(yunet_path),
            "",
            (320, 320),
            config.DET_SCORE_THRESHOLD,
            config.DET_NMS_THRESHOLD,
            config.DET_TOP_K,
        )
        self.recognizer = cv2.FaceRecognizerSF.create(str(sface_path), "")

    def encode(self, img_bgr: np.ndarray, raw_bytes: bytes) -> FaceResult:
        if img_bgr is None:
            raise ValueError("No image provided.")
        h, w = img_bgr.shape[:2]
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(img_bgr)
        if faces is None or len(faces) == 0:
            raise ValueError("No face detected in the image.")

        faces = np.asarray(faces, dtype=np.float32)
        best_idx = int(np.argmax(faces[:, -1]))     # last column = confidence
        best = faces[best_idx]
        x, y, fw, fh = (int(round(v)) for v in best[:4])
        score = float(best[-1])

        aligned = self.recognizer.alignCrop(img_bgr, best)
        feat = self.recognizer.feature(aligned)     # (1, 128) float32
        embedding = np.asarray(feat, dtype=np.float32).reshape(-1)

        return FaceResult(
            bbox=(x, y, fw, fh),
            score=score,
            embedding=embedding,
            embedding_sha256=sha256_bytes(embedding.tobytes()),
            image_sha256=sha256_bytes(raw_bytes),
            aligned_crop=aligned,
            num_faces=int(len(faces)),
        )

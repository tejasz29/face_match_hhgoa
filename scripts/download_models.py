"""CLI: download the OpenCV face models into ./models."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from facematch.models import ensure_models  # noqa: E402

if __name__ == "__main__":
    ensure_models()
    print("Models ready.")

"""API helpers: env and paths."""
import os
from pathlib import Path

# When running as uvicorn from repo root or from src/api, project root is predictable
_API_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _API_DIR.parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "trained"


def get_env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if (v is not None and v != "") else default

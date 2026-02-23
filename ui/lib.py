"""
UI logic: config, data loading, and recommendations.
No Streamlit imports — use from app.py or other frontends.
"""
import os
import pickle
from pathlib import Path
from functools import lru_cache

import pandas as pd
import requests

# Project root (parent of ui/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models" / "trained"

APP_ENV = os.getenv("APP_ENV", "dev").strip().lower()
ENV_FILES = {"dev": ".env.dev", "test": ".env.test", "prod": ".env.prod"}


def load_env_file():
    """Load APP_ENV-specific .env file from project root."""
    env_name = ENV_FILES.get(APP_ENV, ".env.dev")
    env_path = PROJECT_ROOT / env_name
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def get_env(name, default=None):
    value = os.getenv(name)
    if value is not None and value != "":
        return value
    return default


def get_required_env(name):
    value = get_env(name)
    if value:
        return value
    env_file = ENV_FILES.get(APP_ENV, ".env.dev")
    raise RuntimeError(
        f"Missing required env var '{name}'. Set it in {env_file} or the environment."
    )


# Load once when module is imported
load_env_file()

# Config (after load_env_file)
TMDB_API_KEY = get_required_env("TMDB_API_KEY")
DEFAULT_POSTER = "https://via.placeholder.com/500x750.png?text=No+Poster+Available"


def _is_lfs_pointer(path):
    """True if file is a Git LFS pointer (text), not a real pickle."""
    p = Path(path)
    if not p.exists() or p.stat().st_size > 1000:
        return False
    try:
        return p.read_bytes()[:20].startswith(b"version http")
    except Exception:
        return False


def _find_pickle(name):
    """Return path to real pickle in models/trained only. Skip LFS pointers."""
    p = MODELS_DIR / name
    if p.exists() and not _is_lfs_pointer(p):
        return p
    return None


def _load_pickle(path):
    """Load pickle from path. Prefer full read to avoid truncated stream errors."""
    path = Path(path)
    try:
        data = path.read_bytes()
    except Exception as e:
        raise IOError(f"Could not read {path}: {e}") from e
    if not data:
        raise ValueError(f"{path} is empty.")
    try:
        return pickle.loads(data)
    except (EOFError, pickle.UnpicklingError) as e:
        size_mb = len(data) / (1024 * 1024)
        raise ValueError(
            f"{path} appears truncated or corrupted (size {size_mb:.2f} MB). "
            "Re-save the file from your notebook (e.g. pickle.dump(...)) or restore from a full copy."
        ) from e


def load_movies_and_similarity():
    """
    Load movies DataFrame and similarity matrix from models/trained/.
    Skips Git LFS pointer files (uses real .pkl only).
    Returns (movies_df, similarity).
    """
    movies_dic_path = _find_pickle("movies_dic.pkl")
    tag_similarity_path = _find_pickle("tag_similarity.pkl")

    if not movies_dic_path:
        raise FileNotFoundError(
            "movies_dic.pkl not found (or only LFS pointer). "
            f"Put the real movies_dic.pkl in {MODELS_DIR}."
        )
    if not tag_similarity_path:
        raise FileNotFoundError(
            "tag_similarity.pkl not found (or only LFS pointer). "
            f"Put the real tag_similarity.pkl in {MODELS_DIR}."
        )

    movies_dic = _load_pickle(movies_dic_path)
    similarity = _load_pickle(tag_similarity_path)

    # Build movies DataFrame
    if isinstance(movies_dic, dict):
        try:
            movies_df = pd.DataFrame(movies_dic)
        except Exception:
            movies_df = pd.DataFrame.from_dict(movies_dic, orient="index")
    else:
        movies_df = pd.DataFrame(movies_dic)

    if "title" not in movies_df.columns:
        if "name" in movies_df.columns:
            movies_df["title"] = movies_df["name"]
        elif "movie_title" in movies_df.columns:
            movies_df["title"] = movies_df["movie_title"]
        else:
            movies_df["title"] = movies_df.index.astype(str)
    if "id" not in movies_df.columns:
        if "movie_id" in movies_df.columns:
            movies_df["id"] = movies_df["movie_id"]
        else:
            movies_df["id"] = range(len(movies_df))
    movies_df["id"] = pd.to_numeric(movies_df["id"], errors="coerce").fillna(0).astype(int)

    if len(similarity) != len(movies_df):
        raise ValueError(
            f"Similarity length ({len(similarity)}) != movies count ({len(movies_df)})"
        )

    return movies_df, similarity


@lru_cache(maxsize=2048)
def fetch_poster(movie_id: int):
    """Fetch poster URL from TMDB; return DEFAULT_POSTER on failure. Cached by movie_id."""
    try:
        url = (
            f"https://api.themoviedb.org/3/movie/{movie_id}"
            f"?api_key={TMDB_API_KEY}&language=en-US"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        path = data.get("poster_path")
        if path:
            return f"https://image.tmdb.org/t/p/w500{path}"
    except Exception:
        pass
    return DEFAULT_POSTER


@lru_cache(maxsize=1)
def get_featured_posters(count: int = 3):
    """
    Fetch trending movie posters from TMDB for the default/empty state.
    Returns list of {"title": str, "poster": str}; uses cache so we don't hit API every load.
    """
    try:
        url = (
            "https://api.themoviedb.org/3/trending/movie/week"
            f"?api_key={TMDB_API_KEY}&language=en-US"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        out = []
        for item in results[: max(count, 6)]:
            poster_path = item.get("poster_path")
            title = item.get("title") or item.get("name") or "Movie"
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                out.append({"title": title, "poster": poster_url})
            if len(out) >= count:
                break
        return out[:count]
    except Exception:
        pass
    return []


def get_recommendations(movies_df, similarity, selected_title, top_n=5):
    """
    Return list of dicts: [{"title": str, "poster": str, "score_pct": int}, ...].
    score_pct is a 0–100 match score derived from the similarity matrix.
    """
    idx = movies_df[movies_df["title"] == selected_title].index[0]
    row = similarity[idx]
    if hasattr(row, "tolist"):
        row = row.tolist()
    enumerated = list(enumerate(row))
    enumerated.sort(key=lambda x: float(x[1]), reverse=True)
    # Normalize scores to 70–99% for display (similarity may be 0–1 or cosine)
    scores = [float(s) for _, s in enumerated[1 : top_n + 1]]
    min_s = min(scores) if scores else 0.0
    max_s = max(scores) if scores else 1.0
    range_s = (max_s - min_s) if (max_s > min_s) else 1.0
    out = []
    for k, (i, raw_score) in enumerate(enumerated[1 : top_n + 1]):
        movie = movies_df.iloc[i]
        raw = float(raw_score)
        # Map [min_s, max_s] -> [70, 99]; if all same, use 85
        score_pct = int(70 + 29 * (raw - min_s) / range_s) if range_s > 0 else 85
        score_pct = min(99, max(70, score_pct))  # clamp 70–99 so never 0
        out.append({
            "title": movie["title"],
            "poster": fetch_poster(int(movie["id"])),
            "score_pct": score_pct,
        })
    return out

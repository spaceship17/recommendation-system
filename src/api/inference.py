"""
Recommendation inference: load movies_dic + tag_similarity from models/trained,
return top-N similar movies (optionally with poster URLs if TMDB_API_KEY set).
"""
import pickle
from pathlib import Path

import pandas as pd
import requests

from .schemas import MovieRecommendation
from .utils import MODELS_DIR, get_env

MOVIES_DIC_PATH = Path(MODELS_DIR) / "movies_dic.pkl"
TAG_SIMILARITY_PATH = MODELS_DIR / "tag_similarity.pkl"

_movies_df = None
_similarity = None
_load_error: str | None = None
_TMDB_API_KEY: str | None = None
_DEFAULT_POSTER = "https://via.placeholder.com/500x750.png?text=No+Poster"


def _try_load_artifacts() -> None:
    global _movies_df, _similarity, _load_error, _TMDB_API_KEY
    if _movies_df is not None and _similarity is not None:
        return
    _TMDB_API_KEY = get_env("TMDB_API_KEY")
    try:
        with open(MOVIES_DIC_PATH, "rb") as f:
            movies_dic = pickle.load(f)
        with open(TAG_SIMILARITY_PATH, "rb") as f:
            sim = pickle.load(f)
        if isinstance(movies_dic, dict):
            try:
                _movies_df = pd.DataFrame(movies_dic)
            except Exception:
                _movies_df = pd.DataFrame.from_dict(movies_dic, orient="index")
        else:
            _movies_df = pd.DataFrame(movies_dic)
        if "title" not in _movies_df.columns and "name" in _movies_df.columns:
            _movies_df["title"] = _movies_df["name"]
        elif "title" not in _movies_df.columns:
            _movies_df["title"] = _movies_df.index.astype(str)
        if "id" not in _movies_df.columns and "movie_id" in _movies_df.columns:
            _movies_df["id"] = _movies_df["movie_id"]
        elif "id" not in _movies_df.columns:
            _movies_df["id"] = range(len(_movies_df))
        _movies_df["id"] = pd.to_numeric(_movies_df["id"], errors="coerce").fillna(0).astype(int)
        _similarity = sim
        _load_error = None
    except Exception as e:
        _movies_df = None
        _similarity = None
        _load_error = str(e)


def _fetch_poster(movie_id: int) -> str:
    if not _TMDB_API_KEY:
        return _DEFAULT_POSTER
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={_TMDB_API_KEY}&language=en-US"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        path = data.get("poster_path")
        if path:
            return f"https://image.tmdb.org/t/p/w500{path}"
    except Exception:
        pass
    return _DEFAULT_POSTER


def is_model_loaded() -> bool:
    _try_load_artifacts()
    return _movies_df is not None and _similarity is not None


def get_recommendations(movie_title: str, top_n: int = 5) -> list[MovieRecommendation]:
    """Return list of recommended movies with optional poster and score_pct."""
    _try_load_artifacts()
    if _movies_df is None or _similarity is None:
        raise RuntimeError(
            "Model artifacts not loaded. "
            f"Expected {MOVIES_DIC_PATH} and {TAG_SIMILARITY_PATH}. "
            f"Error: {_load_error}"
        )
    match = _movies_df[_movies_df["title"] == movie_title]
    if match.empty:
        raise ValueError(f"Movie not found: {movie_title}")
    idx = match.index[0]
    row = _similarity[idx]
    if hasattr(row, "tolist"):
        row = row.tolist()
    enumerated = list(enumerate(row))
    enumerated.sort(key=lambda x: float(x[1]), reverse=True)
    scores = [float(s) for _, s in enumerated[1 : top_n + 1]]
    min_s = min(scores) if scores else 0.0
    max_s = max(scores) if scores else 1.0
    range_s = (max_s - min_s) if (max_s > min_s) else 1.0
    out = []
    for i, raw_score in enumerated[1 : top_n + 1]:
        movie = _movies_df.iloc[i]
        raw = float(raw_score)
        score_pct = int(70 + 29 * (raw - min_s) / range_s) if range_s > 0 else 85
        score_pct = min(99, max(70, score_pct))
        poster = _fetch_poster(int(movie["id"]))
        out.append(
            MovieRecommendation(
                title=str(movie["title"]),
                poster_url=poster,
                score_pct=score_pct,
            )
        )
    return out[:top_n]

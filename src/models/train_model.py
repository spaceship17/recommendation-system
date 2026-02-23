"""
Training step: build tag similarity matrix and save artifacts to models/trained.
Reads featured CSV (id, title, tags), fits CountVectorizer, computes cosine_similarity,
saves movies_dic.pkl, tag_similarity.pkl, movies.pkl.
"""
import argparse
import logging
import pickle
from pathlib import Path

import pandas as pd
import yaml
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("train-model")


def load_config(config_path: str) -> dict:
    """Load pipeline config YAML."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def train_and_save(
    featured_csv: str,
    models_dir: str,
    max_features: int = 20000,
    stop_words: str = "english",
    movies_dic_name: str = "movies_dic.pkl",
    tag_similarity_name: str = "tag_similarity.pkl",
    movies_name: str = "movies.pkl",
) -> None:
    """Build similarity matrix and save all artifacts."""
    logger.info("Loading featured data from %s", featured_csv)
    df = pd.read_csv(featured_csv)
    if "tags" not in df.columns or "title" not in df.columns or "id" not in df.columns:
        raise ValueError("Featured CSV must have columns: id, title, tags")

    logger.info("Fitting CountVectorizer (max_features=%s)", max_features)
    count_vec = CountVectorizer(max_features=max_features, stop_words=stop_words)
    vector = count_vec.fit_transform(df["tags"].values.astype("U")).toarray()

    logger.info("Computing cosine similarity (shape=%s)", vector.shape)
    tag_similarity = cosine_similarity(vector)

    out_dir = Path(models_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    movies_dic_path = out_dir / movies_dic_name
    tag_similarity_path = out_dir / tag_similarity_name
    movies_path = out_dir / movies_name

    df_new = df[["id", "title", "tags"]].copy()
    with open(movies_dic_path, "wb") as f:
        pickle.dump(df_new.to_dict(), f)
    logger.info("Saved %s", movies_dic_path)

    with open(tag_similarity_path, "wb") as f:
        pickle.dump(tag_similarity, f)
    logger.info("Saved %s", tag_similarity_path)

    with open(movies_path, "wb") as f:
        pickle.dump(df_new, f)
    logger.info("Saved %s", movies_path)


def main():
    parser = argparse.ArgumentParser(description="Train movie similarity model.")
    parser.add_argument("--config", required=True, help="Path to model_config.yaml")
    parser.add_argument("--featured-csv", default=None, help="Override featured CSV path from config")
    parser.add_argument("--models-dir", default=None, help="Override models dir from config")
    args = parser.parse_args()

    config = load_config(args.config)
    data_cfg = config.get("data", {})
    model_cfg = config.get("model", {})

    featured_csv = args.featured_csv or data_cfg.get("featured_file", "data/processed/movies_with_tags.csv")
    models_dir = args.models_dir or model_cfg.get("models_dir", "models/trained")

    train_and_save(
        featured_csv=featured_csv,
        models_dir=models_dir,
        max_features=model_cfg.get("max_features", 20000),
        stop_words=model_cfg.get("stop_words", "english"),
        movies_dic_name=model_cfg.get("movies_dic_name", "movies_dic.pkl"),
        tag_similarity_name=model_cfg.get("tag_similarity_name", "tag_similarity.pkl"),
        movies_name=model_cfg.get("movies_name", "movies.pkl"),
    )


if __name__ == "__main__":
    main()

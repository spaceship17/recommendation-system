"""
Feature engineering step: build tags (overview + genre) for similarity.
Output is used by train_model to compute CountVectorizer + cosine_similarity.
"""
import argparse
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("feature-engineering")


def build_tags(df: pd.DataFrame) -> pd.DataFrame:
    """Create tags column from overview + genre for vectorization."""
    logger.info("Building tags from overview + genre")
    df = df.copy()
    df["tags"] = (df["overview"].astype(str).fillna("") + " " + df["genre"].astype(str).fillna(""))
    return df


def run_engineering(input_file: str, output_file: str) -> pd.DataFrame:
    """Load cleaned data -> build tags -> save (id, title, tags)."""
    logger.info("Loading from %s", input_file)
    df = pd.read_csv(input_file)
    df = build_tags(df)
    out = df[["id", "title", "tags"]].copy()
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_file, index=False)
    logger.info("Saved featured data to %s (shape=%s)", output_file, out.shape)
    return out


def main():
    parser = argparse.ArgumentParser(description="Feature engineering for movie pipeline.")
    parser.add_argument("--input", required=True, help="Path to cleaned CSV")
    parser.add_argument("--output", required=True, help="Path for output CSV (id, title, tags)")
    args = parser.parse_args()
    run_engineering(args.input, args.output)


if __name__ == "__main__":
    main()

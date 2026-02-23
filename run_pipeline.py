"""
Pipeline runner: run data -> features -> train in order (DAG-style).
Usage:
  python run_pipeline.py --config configs/model_config.yaml [--steps data,features,train]
  python run_pipeline.py --config configs/model_config.yaml --steps train  # only train
"""
import argparse
import logging
import sys
from pathlib import Path

import yaml

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("pipeline")


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def run_step_data(config: dict) -> None:
    from src.data.run_processing import run_processing
    data_cfg = config.get("data", {})
    run_processing(
        input_file=data_cfg["raw_file"],
        output_file=data_cfg["processed_file"],
    )


def run_step_features(config: dict) -> None:
    from src.features.engineer import run_engineering
    data_cfg = config.get("data", {})
    run_engineering(
        input_file=data_cfg["processed_file"],
        output_file=data_cfg["featured_file"],
    )


def run_step_train(config: dict) -> None:
    from src.models.train_model import train_and_save
    model_cfg = config.get("model", {})
    data_cfg = config.get("data", {})
    train_and_save(
        featured_csv=data_cfg["featured_file"],
        models_dir=model_cfg["models_dir"],
        max_features=model_cfg.get("max_features", 20000),
        stop_words=model_cfg.get("stop_words", "english"),
        movies_dic_name=model_cfg.get("movies_dic_name", "movies_dic.pkl"),
        tag_similarity_name=model_cfg.get("tag_similarity_name", "tag_similarity.pkl"),
        movies_name=model_cfg.get("movies_name", "movies.pkl"),
    )


def main():
    parser = argparse.ArgumentParser(description="Run movie recommendation pipeline (data -> features -> train).")
    parser.add_argument("--config", default="configs/model_config.yaml", help="Path to model_config.yaml")
    parser.add_argument(
        "--steps",
        default="data,features,train",
        help="Comma-separated steps: data, features, train (default: all)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    steps = [s.strip() for s in args.steps.split(",") if s.strip()]

    step_fns = {
        "data": run_step_data,
        "features": run_step_features,
        "train": run_step_train,
    }
    for step in steps:
        if step not in step_fns:
            logger.error("Unknown step: %s. Choose from: %s", step, list(step_fns))
            sys.exit(1)
        logger.info("Running step: %s", step)
        step_fns[step](config)
    logger.info("Pipeline finished: %s", steps)


if __name__ == "__main__":
    main()

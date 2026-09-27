"""Command-line entry points for the project."""

import argparse
from pathlib import Path

from sentiment_analysis.data import load_dataset
from sentiment_analysis.eda import summarize, write_report
from sentiment_analysis.evaluation import evaluate_predictions, write_evaluation_report
from sentiment_analysis.model import train_naive_bayes_from_artifacts
from sentiment_analysis.preprocessing import preprocess_dataset
from sentiment_analysis.vectorization import save_vectorized_artifacts, vectorize_splits


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="E-learning sentiment analysis")
    parser.add_argument("--version", action="version", version="0.1.0")
    parser.add_argument("--task", choices=("preprocess", "train-naive-bayes"), default="preprocess")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--vectorized-dir", type=Path, default=Path("data/processed/vectorized"))
    parser.add_argument("--report", type=Path, default=Path("reports/eda_report.md"))
    parser.add_argument("--model-path", type=Path, default=Path("models/naive_bayes_tfidf.joblib"))
    parser.add_argument("--model-report", type=Path, default=Path("reports/naive_bayes_dev.md"))
    parser.add_argument("--alpha", type=float, default=1.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.task == "train-naive-bayes":
        model, y_dev, predictions, features = train_naive_bayes_from_artifacts(
            args.vectorized_dir,
            args.model_path,
            alpha=args.alpha,
        )
        metrics = evaluate_predictions(y_dev, predictions)
        write_evaluation_report(
            metrics,
            args.model_report,
            model_name="Multinomial Naive Bayes",
            alpha=model.alpha,
            split="dev",
            samples=len(y_dev),
            features=features,
        )
        print(f"Trained MultinomialNB(alpha={model.alpha:g}) on train; evaluated on {len(y_dev):,} dev samples.")
        print(f"Dev accuracy: {metrics['accuracy']:.4f}; macro-F1: {metrics['macro_f1']:.4f}")
        print(f"Saved model: {args.model_path}")
        print(f"Saved report: {args.model_report}")
        print("Test split was not loaded or evaluated.")
        return

    raw = load_dataset(args.data_dir)
    processed = preprocess_dataset(raw)
    args.processed_dir.mkdir(parents=True, exist_ok=True)
    processed.to_csv(
        args.processed_dir / "dataset_preprocessed.csv",
        index=False,
        encoding="utf-8-sig",
    )
    vectorizer, x_by_split, y_by_split = vectorize_splits(processed)
    save_vectorized_artifacts(vectorizer, x_by_split, y_by_split, args.vectorized_dir)
    write_report(summarize(processed), args.report)
    print(f"Loaded {len(raw):,} samples; wrote {len(processed):,} cleaned samples.")
    print(f"Preprocessed data: {args.processed_dir / 'dataset_preprocessed.csv'}")
    print(f"TF-IDF artifacts: {args.vectorized_dir}")
    print(f"EDA report: {args.report}")


if __name__ == "__main__":
    main()

"""Command-line entry points for the project."""

import argparse
from pathlib import Path

from sentiment_analysis.data import load_dataset
from sentiment_analysis.eda import summarize, write_report
from sentiment_analysis.evaluation import evaluate_predictions, write_evaluation_report
from sentiment_analysis.model import train_naive_bayes_from_artifacts, train_svm_from_artifacts
from sentiment_analysis.preprocessing import preprocess_dataset
from sentiment_analysis.vectorization import save_vectorized_artifacts, vectorize_splits


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="E-learning sentiment analysis")
    parser.add_argument("--version", action="version", version="0.1.0")
    parser.add_argument("--task", choices=("preprocess", "train-naive-bayes", "train-svm"), default="preprocess")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--vectorized-dir", type=Path, default=Path("data/processed/vectorized"))
    parser.add_argument("--report", type=Path, default=Path("reports/eda_report.md"))
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--model-report", type=Path)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--c", type=float, default=1.0)
    parser.add_argument("--class-weight", choices=("balanced", "none"), default="balanced")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.task in {"train-naive-bayes", "train-svm"}:
        is_svm = args.task == "train-svm"
        model_path = args.model_path or Path(
            "models/svm_tfidf.joblib" if is_svm else "models/naive_bayes_tfidf.joblib"
        )
        model_report = args.model_report or Path(
            "reports/svm_dev.md" if is_svm else "reports/naive_bayes_dev.md"
        )
        if is_svm:
            model, y_dev, predictions, features = train_svm_from_artifacts(
                args.vectorized_dir,
                model_path,
                c=args.c,
                class_weight=None if args.class_weight == "none" else args.class_weight,
            )
            model_name = "Linear Support Vector Classifier (LinearSVC)"
        else:
            model, y_dev, predictions, features = train_naive_bayes_from_artifacts(
                args.vectorized_dir,
                model_path,
                alpha=args.alpha,
            )
            model_name = "Multinomial Naive Bayes"
        metrics = evaluate_predictions(y_dev, predictions)
        write_evaluation_report(
            metrics,
            model_report,
            model_name=model_name,
            split="dev",
            samples=len(y_dev),
            features=features,
            alpha=model.alpha if not is_svm else None,
            c=model.C if is_svm else None,
            class_weight=(model.class_weight or "None") if is_svm else None,
        )
        if is_svm:
            weight = model.class_weight or "none"
            print(f"Trained LinearSVC(C={model.C:g}, class_weight={weight}) on train; evaluated on {len(y_dev):,} dev samples.")
        else:
            print(f"Trained MultinomialNB(alpha={model.alpha:g}) on train; evaluated on {len(y_dev):,} dev samples.")
        print(f"Dev accuracy: {metrics['accuracy']:.4f}; macro-F1: {metrics['macro_f1']:.4f}")
        print(f"Saved model: {model_path}")
        print(f"Saved report: {model_report}")
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

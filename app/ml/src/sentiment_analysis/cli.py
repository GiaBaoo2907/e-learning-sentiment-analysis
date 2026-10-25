"""Command-line entry points for the project."""

import argparse
import json
from pathlib import Path

from sentiment_analysis.data import load_dataset
from sentiment_analysis.eda import summarize, write_report
from sentiment_analysis.error_analysis import analyze_dev_errors
from sentiment_analysis.evaluation import evaluate_predictions, write_evaluation_report
from sentiment_analysis.model import (
    train_logistic_regression_from_artifacts,
    train_naive_bayes_from_artifacts,
    train_svm_from_artifacts,
)
from sentiment_analysis.preprocessing import preprocess_dataset
from sentiment_analysis.vectorization import save_vectorized_artifacts, vectorize_splits
from sentiment_analysis.visualization import plot_model_comparison


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="E-learning sentiment analysis")
    parser.add_argument("--version", action="version", version="0.1.0")
    parser.add_argument(
        "--task",
        choices=(
            "preprocess",
            "train-naive-bayes",
            "train-svm",
            "train-logistic-regression",
            "analyze-errors",
            "compare-models",
        ),
        default="preprocess",
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--vectorized-dir", type=Path, default=Path("data/processed/vectorized"))
    parser.add_argument(
        "--text-column",
        choices=("text_segmented", "text_no_stopword"),
        default="text_segmented",
        help="Text representation to use when generating TF-IDF artifacts.",
    )
    parser.add_argument(
        "--ngram-setting",
        choices=("unigram", "unigram-bigram"),
        default="unigram-bigram",
        help="TF-IDF n-gram range for preprocessing experiments.",
    )
    parser.add_argument("--report", type=Path, default=Path("app/ml/reports/eda_report.md"))
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--model-report", type=Path)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--c", type=float, default=1.0)
    parser.add_argument("--class-weight", choices=("balanced", "none"), default="balanced")
    parser.add_argument("--error-examples-per-confusion", type=int, default=3)
    parser.add_argument("--chart-dir", type=Path, default=Path("app/ml/reports/figures"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.task == "analyze-errors":
        model_path = args.model_path or Path("data/models/experiments/linear_svm_c_1_balanced.joblib")
        report_path = args.model_report or Path("app/ml/reports/error_analysis_dev.md")
        results = analyze_dev_errors(
            model_path,
            args.vectorized_dir,
            args.processed_dir / "dataset_preprocessed.csv",
            report_path,
            examples_per_confusion=args.error_examples_per_confusion,
        )
        print(
            f"Analyzed {results['samples']:,} dev samples; "
            f"errors: {results['errors']:,}; accuracy: {results['accuracy']:.4f}; "
            f"macro-F1: {results['macro_f1']:.4f}."
        )
        print(f"Saved error analysis: {report_path}")
        print(f"Saved error samples: {results['error_samples_path']}")
        print("Test split was not loaded or evaluated.")
        return

    if args.task == "compare-models":
        model_paths = {
            "Naive Bayes": Path("data/models/experiments/naive_bayes_alpha_0_1.joblib"),
            "LinearSVC": Path("data/models/experiments/linear_svm_c_1_balanced.joblib"),
            "Logistic Regression": Path("data/models/experiments/logistic_regression_c_10_balanced.joblib"),
        }
        metric_path, confusion_path = plot_model_comparison(
            model_paths,
            args.vectorized_dir,
            args.chart_dir,
        )
        print(f"Saved dev metric comparison: {metric_path}")
        print(f"Saved dev confusion matrices: {confusion_path}")
        print("Test split was not loaded or evaluated.")
        return

    if args.task in {"train-naive-bayes", "train-svm", "train-logistic-regression"}:
        is_svm = args.task == "train-svm"
        is_logistic_regression = args.task == "train-logistic-regression"
        model_path = args.model_path or Path(
            "data/models/svm_tfidf.joblib"
            if is_svm
            else "data/models/logistic_regression_tfidf.joblib"
            if is_logistic_regression
            else "data/models/naive_bayes_tfidf.joblib"
        )
        model_report = args.model_report or Path(
            "app/ml/reports/svm_dev.md"
            if is_svm
            else "app/ml/reports/logistic_regression_dev.md"
            if is_logistic_regression
            else "app/ml/reports/naive_bayes_dev.md"
        )
        if is_svm:
            model, y_dev, predictions, features = train_svm_from_artifacts(
                args.vectorized_dir,
                model_path,
                c=args.c,
                class_weight=None if args.class_weight == "none" else args.class_weight,
            )
            model_name = "Linear Support Vector Classifier (LinearSVC)"
        elif is_logistic_regression:
            model, y_dev, predictions, features = train_logistic_regression_from_artifacts(
                args.vectorized_dir,
                model_path,
                c=args.c,
                class_weight=None if args.class_weight == "none" else args.class_weight,
            )
            model_name = "Logistic Regression"
        else:
            model, y_dev, predictions, features = train_naive_bayes_from_artifacts(
                args.vectorized_dir,
                model_path,
                alpha=args.alpha,
            )
            model_name = "Multinomial Naive Bayes"
        metrics = evaluate_predictions(y_dev, predictions)
        metadata_path = args.vectorized_dir / "metadata.json"
        vectorized_metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.is_file()
            else {}
        )
        write_evaluation_report(
            metrics,
            model_report,
            model_name=model_name,
            split="dev",
            samples=len(y_dev),
            features=features,
            alpha=model.alpha if not is_svm and not is_logistic_regression else None,
            c=model.C if is_svm or is_logistic_regression else None,
            class_weight=(model.class_weight or "None") if is_svm or is_logistic_regression else None,
            solver=model.solver if is_logistic_regression else None,
            text_column=vectorized_metadata.get("text_column", "unknown"),
        )
        if is_svm:
            weight = model.class_weight or "none"
            print(f"Trained LinearSVC(C={model.C:g}, class_weight={weight}) on train; evaluated on {len(y_dev):,} dev samples.")
        elif is_logistic_regression:
            weight = model.class_weight or "none"
            print(f"Trained LogisticRegression(C={model.C:g}, class_weight={weight}, solver={model.solver}) on train; evaluated on {len(y_dev):,} dev samples.")
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
    vectorizer, x_by_split, y_by_split = vectorize_splits(
        processed,
        text_column=args.text_column,
        ngram_range=(1, 1) if args.ngram_setting == "unigram" else (1, 2),
    )
    save_vectorized_artifacts(
        vectorizer,
        x_by_split,
        y_by_split,
        args.vectorized_dir,
        text_column=args.text_column,
    )
    write_report(summarize(processed), args.report)
    print(f"Loaded {len(raw):,} samples; wrote {len(processed):,} cleaned samples.")
    print(f"Preprocessed data: {args.processed_dir / 'dataset_preprocessed.csv'}")
    print(f"TF-IDF artifacts: {args.vectorized_dir}")
    print(f"EDA report: {args.report}")


if __name__ == "__main__":
    main()

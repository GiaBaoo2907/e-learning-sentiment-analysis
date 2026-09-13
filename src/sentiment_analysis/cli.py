"""Command-line entry points for the project."""

import argparse
from pathlib import Path

from sentiment_analysis.data import load_dataset
from sentiment_analysis.eda import summarize, write_report
from sentiment_analysis.preprocessing import preprocess_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="E-learning sentiment analysis")
    parser.add_argument("--version", action="version", version="0.1.0")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--report", type=Path, default=Path("reports/eda_report.md"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    raw = load_dataset(args.data_dir)
    processed = preprocess_dataset(raw)
    args.processed_dir.mkdir(parents=True, exist_ok=True)
    processed.to_csv(args.processed_dir / "dataset_clean.csv", index=False, encoding="utf-8-sig")
    processed.to_csv(
        args.processed_dir / "dataset_preprocessed.csv",
        index=False,
        encoding="utf-8-sig",
    )
    write_report(summarize(processed), args.report)
    print(f"Loaded {len(raw):,} samples; wrote {len(processed):,} cleaned samples.")
    print(f"Processed data: {args.processed_dir / 'dataset_clean.csv'}")
    print(f"Preprocessed data: {args.processed_dir / 'dataset_preprocessed.csv'}")
    print(f"EDA report: {args.report}")


if __name__ == "__main__":
    main()

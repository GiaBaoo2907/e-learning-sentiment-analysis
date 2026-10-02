"""Metrics and reports for classifier evaluation."""

from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score


CLASS_NAMES = {0: "negative", 1: "neutral", 2: "positive"}


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
	"""Calculate accuracy, macro-F1, per-class metrics, and confusion matrix."""
	labels = sorted(CLASS_NAMES)
	return {
		"accuracy": float(accuracy_score(y_true, y_pred)),
		"macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
		"per_class": classification_report(
			y_true,
			y_pred,
			labels=labels,
			target_names=[CLASS_NAMES[label] for label in labels],
			output_dict=True,
			zero_division=0,
		),
		"confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels),
		"labels": labels,
	}


def write_evaluation_report(
	metrics: dict[str, Any],
	output_path: str | Path,
	model_name: str,
	split: str,
	samples: int,
	features: int,
	alpha: float | None = None,
	c: float | None = None,
	class_weight: str | None = None,
) -> None:
	"""Write a reproducible Markdown evaluation report."""
	per_class = metrics["per_class"]
	confusion = metrics["confusion_matrix"]
	configuration = []
	if alpha is not None:
		configuration.append(f"| Smoothing alpha | {alpha:g} |")
	if c is not None:
		configuration.extend(
			[
				f"| Regularization parameter C | {c:g} |",
				f"| Class weight | {class_weight or 'None'} |",
			]
		)
	report = [
		f"# {model_name} evaluation ({split})",
		"",
		"## Experiment configuration",
		"",
		"| Item | Value |",
		"|---|---|",
		f"| Estimator | {model_name} |",
		*configuration,
		"| Input features | Existing train-fitted TF-IDF, word uni/bi-grams |",
		"| Training split | train |",
		f"| Evaluation split | {split} |",
		f"| Evaluation samples | {samples:,} |",
		f"| Feature count | {features:,} |",
		"| Test split used | No |",
		"",
		"## Overall metrics",
		"",
		"| Accuracy | Macro-F1 |",
		"|---:|---:|",
		f"| {metrics['accuracy']:.4f} | {metrics['macro_f1']:.4f} |",
		"",
		"## Per-class metrics",
		"",
		"| Class | Precision | Recall | F1 | Support |",
		"|---|---:|---:|---:|---:|",
	]
	for label in metrics["labels"]:
		name = CLASS_NAMES[label]
		values = per_class[name]
		report.append(
			f"| {name} | {values['precision']:.4f} | {values['recall']:.4f} | "
			f"{values['f1-score']:.4f} | {int(values['support'])} |"
		)
	report.extend(
		[
			"",
			"## Confusion matrix",
			"",
			"Rows are actual labels; columns are predicted labels.",
			"",
			"| Actual \\ Predicted | Negative | Neutral | Positive |",
			"|---|---:|---:|---:|",
		]
	)
	for label, row in zip(metrics["labels"], confusion, strict=True):
		report.append(f"| {CLASS_NAMES[label]} | {row[0]} | {row[1]} | {row[2]} |")
	report.extend(
		[
			"",
			"## Interpretation notes",
			"",
			*(
				[
					"- LinearSVC learns a linear maximum-margin decision boundary; C controls the trade-off between margin size and training errors.",
					"- Class weighting adjusts the penalty for mistakes in each class; balanced weights are computed from training labels.",
				]
				if c is not None
				else [
					"- Multinomial Naive Bayes is a probabilistic baseline with conditional feature independence.",
					"- Alpha smoothing prevents zero likelihoods for features unseen in a class.",
					"- TF-IDF values are nonnegative but fractional; treat this as a practical baseline, not literal token counts.",
				]
			),
			"- Dev results support model comparison only; reserve test for final evaluation after model selection.",
		]
	)
	destination = Path(output_path)
	destination.parent.mkdir(parents=True, exist_ok=True)
	destination.write_text("\n".join(report) + "\n", encoding="utf-8")

"""Visualization helpers for comparing sentiment models on dev."""

from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from scipy import sparse
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from sentiment_analysis.evaluation import CLASS_NAMES


MODEL_COLORS = ("#315A72", "#D17A52", "#4C8C78")


def plot_model_comparison(
    model_paths: dict[str, str | Path],
    vectorized_dir: str | Path,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Create dev metric and normalized confusion-matrix comparison plots."""
    artifact_dir = Path(vectorized_dir)
    features = sparse.load_npz(artifact_dir / "X_dev.npz")
    labels = np.load(artifact_dir / "y_dev.npy", allow_pickle=False)
    ordered_labels = sorted(CLASS_NAMES)
    model_names = list(model_paths)
    class_reports = {}
    confusion_matrices = {}
    accuracies = {}

    for model_name, model_path in model_paths.items():
        model = joblib.load(model_path)
        if features.shape[1] != model.n_features_in_:
            raise ValueError(f"Dev feature count does not match model {model_name!r}")
        predictions = model.predict(features)
        class_reports[model_name] = classification_report(
            labels,
            predictions,
            labels=ordered_labels,
            target_names=[CLASS_NAMES[label] for label in ordered_labels],
            output_dict=True,
            zero_division=0,
        )
        confusion_matrices[model_name] = confusion_matrix(
            labels,
            predictions,
            labels=ordered_labels,
        )
        accuracies[model_name] = float(accuracy_score(labels, predictions))

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    metric_path = destination / "model_comparison_dev.png"
    confusion_path = destination / "confusion_matrices_dev.png"

    metric_names = ["negative", "neutral", "positive", "macro avg", "accuracy"]
    metric_labels = ["Negative F1", "Neutral F1", "Positive F1", "Macro-F1", "Accuracy"]
    positions = np.arange(len(metric_names))
    bar_width = 0.8 / len(model_names)
    figure, axis = plt.subplots(figsize=(11, 6.5), layout="constrained")
    for model_index, model_name in enumerate(model_names):
        report = class_reports[model_name]
        values = [float(report[name]["f1-score"]) for name in metric_names[:3]]
        values.extend([float(report["macro avg"]["f1-score"]), accuracies[model_name]])
        offsets = positions + (model_index - (len(model_names) - 1) / 2) * bar_width
        axis.bar(
            offsets,
            values,
            width=bar_width,
            label=model_name,
            color=MODEL_COLORS[model_index % len(MODEL_COLORS)],
        )
    axis.set_title("Model performance on dev", loc="left", weight="bold")
    axis.set_ylabel("Score")
    axis.set_xticks(positions, metric_labels)
    axis.set_ylim(0, 1.08)
    axis.grid(axis="y", color="#D8DEE4", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(frameon=False, ncols=len(model_names), loc="upper center", bbox_to_anchor=(0.5, -0.12))
    figure.savefig(metric_path, dpi=180, facecolor="white")
    plt.close(figure)

    supports = np.bincount(labels, minlength=len(ordered_labels))
    figure, axes = plt.subplots(
        1,
        len(model_names),
        figsize=(5.0 * len(model_names), 5.2),
        squeeze=False,
        layout="constrained",
    )
    image = None
    for axis, model_name in zip(axes[0], model_names, strict=True):
        counts = confusion_matrices[model_name]
        row_totals = counts.sum(axis=1, keepdims=True)
        normalized = np.divide(counts, row_totals, out=np.zeros_like(counts, dtype=float), where=row_totals != 0)
        image = axis.imshow(normalized, vmin=0, vmax=1, cmap="Blues")
        axis.set_title(model_name, loc="left", weight="bold")
        axis.set_xticks(ordered_labels, [CLASS_NAMES[label].title() for label in ordered_labels])
        axis.set_yticks(
            ordered_labels,
            [f"{CLASS_NAMES[label].title()} (n={supports[label]})" for label in ordered_labels],
        )
        axis.set_xlabel("Predicted")
        axis.set_ylabel("Actual")
        for row in range(len(ordered_labels)):
            for column in range(len(ordered_labels)):
                value = normalized[row, column]
                color = "white" if value > 0.55 else "#17212B"
                axis.text(
                    column,
                    row,
                    f"{value:.0%}\n({counts[row, column]})",
                    ha="center",
                    va="center",
                    color=color,
                    fontsize=9,
                )
    figure.colorbar(image, ax=axes.ravel().tolist(), label="Share of actual class", shrink=0.78)
    figure.suptitle("Row-normalized confusion matrices on dev", x=0.02, ha="left", weight="bold")
    figure.savefig(confusion_path, dpi=180, facecolor="white")
    plt.close(figure)
    return metric_path, confusion_path

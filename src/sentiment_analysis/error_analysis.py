"""Dev-set error analysis for saved sentiment classifiers."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score

from sentiment_analysis.evaluation import CLASS_NAMES


TOPIC_NAMES = {
    0: "lecturer",
    1: "training program",
    2: "facility",
    3: "other",
}


def analyze_dev_errors(
    model_path: str | Path,
    vectorized_dir: str | Path,
    processed_data_path: str | Path,
    output_path: str | Path,
    examples_per_confusion: int = 3,
) -> dict[str, object]:
    """Validate artifact alignment, predict dev, and write a diagnostic report."""
    model = joblib.load(model_path)
    artifact_dir = Path(vectorized_dir)
    features = sparse.load_npz(artifact_dir / "X_dev.npz")
    labels = np.load(artifact_dir / "y_dev.npy", allow_pickle=False)
    processed = pd.read_csv(processed_data_path)
    dev = processed.loc[processed["split"].eq("dev")].reset_index(drop=True)

    if len(dev) != len(labels) or features.shape[0] != len(labels):
        raise ValueError("Processed dev rows, dev labels, and dev features are not aligned")
    if not np.array_equal(dev["sentiment"].to_numpy(dtype=np.int64), labels):
        raise ValueError("Processed dev labels do not match saved dev labels")
    if features.shape[1] != model.n_features_in_:
        raise ValueError("Dev feature count does not match the saved model")
    if "topic" not in dev or "text" not in dev:
        raise ValueError("Processed data must include original text and topic columns")

    predictions = model.predict(features)
    labels_ordered = sorted(CLASS_NAMES)
    matrix = confusion_matrix(labels, predictions, labels=labels_ordered)
    overall_accuracy = float(accuracy_score(labels, predictions))
    macro_f1 = float(
        f1_score(labels, predictions, labels=labels_ordered, average="macro", zero_division=0)
    )
    errors = labels != predictions

    report = [
        f"# Error analysis: {type(model).__name__} (dev)",
        "",
        "## Protocol",
        "",
        "- Chỉ dùng dev để phân tích; test không được tải hoặc đánh giá.",
        "- Text, topic, nhãn và feature được kiểm tra số dòng/thứ tự trước khi ghép.",
        f"- Model: `{model_path}`; processed data: `{processed_data_path}`.",
        f"- Samples: {len(labels):,}; features: {features.shape[1]:,}.",
        "",
        "## Overall result",
        "",
        f"- Accuracy: {overall_accuracy:.4f}",
        f"- Macro-F1: {macro_f1:.4f}",
        f"- Errors: {int(errors.sum()):,} / {len(labels):,}",
        "",
        "## Confusion matrix",
        "",
        "Rows are actual labels; columns are predicted labels.",
        "",
        "| Actual \\ Predicted | Negative | Neutral | Positive |",
        "|---|---:|---:|---:|",
    ]
    for label, row in zip(labels_ordered, matrix, strict=True):
        report.append(f"| {CLASS_NAMES[label]} | {row[0]} | {row[1]} | {row[2]} |")

    report.extend(
        [
            "",
            "## Error rate by topic",
            "",
            "| Topic | Samples | Errors | Accuracy | Macro-F1 | Neutral support | Neutral recall |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    topic_values = dev["topic"].to_numpy(dtype=np.int64)
    for topic in sorted(TOPIC_NAMES):
        mask = topic_values == topic
        if not mask.any():
            continue
        topic_labels = labels[mask]
        topic_predictions = predictions[mask]
        report.append(
            f"| {TOPIC_NAMES[topic]} | {int(mask.sum())} | {int((topic_labels != topic_predictions).sum())} | "
            f"{accuracy_score(topic_labels, topic_predictions):.4f} | "
            f"{f1_score(topic_labels, topic_predictions, labels=labels_ordered, average='macro', zero_division=0):.4f} | "
            f"{int(np.count_nonzero(topic_labels == 1))} | "
            f"{recall_score(topic_labels, topic_predictions, labels=[1], average='macro', zero_division=0):.4f} |"
        )

    error_frame = pd.DataFrame(
        {
            "actual": labels,
            "predicted": predictions,
            "topic": topic_values,
            "text": dev["text"].astype(str).to_numpy(),
        }
    )
    error_frame = error_frame.loc[error_frame["actual"] != error_frame["predicted"]].copy()
    error_frame["actual_label"] = error_frame["actual"].map(CLASS_NAMES)
    error_frame["predicted_label"] = error_frame["predicted"].map(CLASS_NAMES)
    error_frame["topic_name"] = error_frame["topic"].map(TOPIC_NAMES)
    error_frame["pair"] = error_frame.apply(
        lambda row: f"{CLASS_NAMES[int(row['actual'])]} → {CLASS_NAMES[int(row['predicted'])]}",
        axis=1,
    )
    error_frame["error_cause"] = ""
    pair_counts = error_frame["pair"].value_counts()
    report.extend(
        [
            "",
            "## Most frequent error directions and examples",
            "",
            "Examples are selected from dev errors for qualitative inspection; they are not automatic explanations.",
            "",
        ]
    )
    for pair, count in pair_counts.head(5).items():
        report.extend([f"### {pair} ({count} samples)", ""])
        examples = error_frame.loc[error_frame["pair"].eq(pair)].head(examples_per_confusion)
        for row in examples.itertuples(index=False):
            text = row.text.replace("|", "\\|").replace("\r", " ").replace("\n", " ")
            report.append(
                f"- Topic: {TOPIC_NAMES.get(int(row.topic), str(row.topic))}; text: {text}"
            )
        report.append("")

    report.extend(
        [
            "## How to use this analysis",
            "",
            "1. Review the largest confusion directions and topic-level metrics first.",
            "2. Read example sentences and manually assign error causes (negation, mixed sentiment, short/ambiguous text, slang/emoji, or annotation ambiguity).",
            "3. Count causes before changing preprocessing or model settings; make one change at a time and re-evaluate on dev.",
            "4. Freeze model and configuration before the one-time final test evaluation.",
            "",
            "Topic-conditioned results are diagnostic only; the classifier predicts sentiment, not topic.",
        ]
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    error_samples_path = destination.with_name(f"{destination.stem}_samples.csv")
    error_frame[
        ["actual_label", "predicted_label", "topic_name", "text", "pair", "error_cause"]
    ].to_csv(error_samples_path, index=False, encoding="utf-8-sig")
    report.append(f"Error sample table for manual annotation: `{error_samples_path}`.")
    destination.write_text("\n".join(report) + "\n", encoding="utf-8")
    return {
        "samples": len(labels),
        "errors": int(errors.sum()),
        "accuracy": overall_accuracy,
        "macro_f1": macro_f1,
        "confusion_matrix": matrix,
        "predictions": predictions,
        "error_samples_path": error_samples_path,
    }

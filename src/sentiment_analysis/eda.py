"""Exploratory summaries for the sentiment dataset."""

from pathlib import Path

import pandas as pd


SENTIMENT_NAMES = {0: "negative", 1: "neutral", 2: "positive"}
TOPIC_NAMES = {0: "lecturer", 1: "training program", 2: "facility", 3: "other"}


def summarize(frame: pd.DataFrame) -> dict[str, object]:
    """Return compact, serializable EDA tables and global measurements."""
    summary_frame = frame.copy()
    if "text_length" not in summary_frame:
        summary_frame["text_length"] = summary_frame["text"].str.len()
    if "word_count" not in summary_frame:
        summary_frame["word_count"] = summary_frame["text"].str.split().str.len()

    sentiment_counts = summary_frame["sentiment"].value_counts().sort_index()
    sentiment_table = pd.DataFrame(
        {
            "label": sentiment_counts.index,
            "name": sentiment_counts.index.map(SENTIMENT_NAMES),
            "count": sentiment_counts.values,
            "percent": (sentiment_counts.values / len(summary_frame) * 100).round(2),
        }
    )
    split_table = (
        summary_frame.groupby("split", sort=False)
        .agg(
            samples=("text", "size"),
            average_characters=("text_length", "mean"),
            average_words=("word_count", "mean"),
        )
        .round(2)
        .reset_index()
    )
    topic_counts = summary_frame["topic"].value_counts().sort_index()
    topic_table = pd.DataFrame(
        {
            "label": topic_counts.index,
            "name": topic_counts.index.map(TOPIC_NAMES),
            "count": topic_counts.values,
            "percent": (topic_counts.values / len(summary_frame) * 100).round(2),
        }
    )
    return {
        "samples": len(summary_frame),
        "average_characters": round(float(summary_frame["text_length"].mean()), 2),
        "average_words": round(float(summary_frame["word_count"].mean()), 2),
        "sentiments": sentiment_table,
        "topics": topic_table,
        "splits": split_table,
    }


def write_report(summary: dict[str, object], output_path: str | Path) -> None:
    """Write the EDA summary as a short Markdown report."""
    sentiments = summary["sentiments"]
    topics = summary["topics"]
    splits = summary["splits"]
    report = [
        "# Báo cáo EDA dataset phản hồi e-learning",
        "",
        f"- Tổng số mẫu: **{summary['samples']:,}**",
        f"- Độ dài trung bình: **{summary['average_characters']:.2f} ký tự** / **{summary['average_words']:.2f} từ**",
        "",
        "## Phân bố cảm xúc",
        "",
        "| Nhãn | Ý nghĩa | Số mẫu | Tỷ lệ |",
        "|---:|---|---:|---:|",
    ]
    report.extend(
        f"| {row.label} | {row['name']} | {row['count']:,} | {row['percent']:.2f}% |"
        for _, row in sentiments.iterrows()
    )
    report.extend(["", "## Phân bố topic", "", "| Nhãn | Ý nghĩa | Số mẫu | Tỷ lệ |", "|---:|---|---:|---:|"])
    report.extend(
        f"| {row.label} | {row['name']} | {row['count']:,} | {row['percent']:.2f}% |"
        for _, row in topics.iterrows()
    )
    report.extend(["", "## Theo tập dữ liệu", "", "| Tập | Số mẫu | Ký tự trung bình | Từ trung bình |", "|---|---:|---:|---:|"])
    report.extend(
        f"| {row['split']} | {row['samples']:,} | {row['average_characters']:.2f} | {row['average_words']:.2f} |"
        for _, row in splits.iterrows()
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(report) + "\n", encoding="utf-8")
from pathlib import Path

import pandas as pd

from sentiment_analysis.data import load_dataset
from sentiment_analysis.eda import summarize
from sentiment_analysis.preprocessing import clean_text, preprocess_dataset, remove_stopwords, segment_text


DATA_DIR = Path(__file__).parents[1] / "data"


def test_dataset_splits_are_aligned() -> None:
    frame = load_dataset(DATA_DIR)
    assert len(frame) == 16175
    assert set(frame["split"]) == {"train", "dev", "test"}
    assert frame[["text", "sentiment", "topic"]].notna().all().all()


def test_clean_text_preserves_vietnamese_and_normalizes_noise() -> None:
    assert clean_text("  HỌC   RẤT TỐT! https://example.com ") == "học rất tốt! URL"


def test_preprocessing_is_vectorization_ready() -> None:
    frame = pd.DataFrame(
        {
            "text": ["  Học tốt  ", "Học tốt", ""],
            "sentiment": [2, 2, 1],
            "topic": [0, 0, 1],
            "split": ["train", "train", "dev"],
        }
    )
    processed = preprocess_dataset(frame)
    assert len(processed) == 1
    assert {"text_clean", "text_segmented", "text_no_stopword", "text_length", "word_count"}.issubset(processed.columns)


def test_vietnamese_segmentation_and_stopwords_keep_negation() -> None:
    segmented = segment_text("giảng viên rất nhiệt tình")
    assert "giảng_viên" in segmented
    assert "nhiệt_tình" in segmented
    assert "không" in remove_stopwords("không tốt và rất vui")


def test_eda_reports_sample_count_and_label_distribution() -> None:
    summary = summarize(load_dataset(DATA_DIR))
    assert summary["samples"] == 16175
    assert summary["sentiments"]["count"].sum() == 16175
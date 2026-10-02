from pathlib import Path

import pandas as pd

from sentiment_analysis.data import load_dataset
from sentiment_analysis.eda import summarize
from sentiment_analysis.evaluation import evaluate_predictions
from sentiment_analysis.model import train_naive_bayes_from_artifacts, train_svm_from_artifacts
from sentiment_analysis.preprocessing import clean_text, preprocess_dataset, remove_stopwords, segment_text
from sentiment_analysis.vectorization import vectorize_splits


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


def test_tfidf_fits_train_only_and_transforms_other_splits() -> None:
    frame = pd.DataFrame(
        {
            "text_segmented": [
                "giảng_viên tốt nhiệt_tình",
                "môn_học nội_dung tốt",
                "devtoken hoàn_toàn_mới",
                "testtoken khác_biệt",
            ],
            "sentiment": [2, 2, 1, 0],
            "split": ["train", "train", "dev", "test"],
        }
    )
    vectorizer, x_by_split, y_by_split = vectorize_splits(frame, min_df=1)

    assert "devtoken" not in vectorizer.vocabulary_
    assert "testtoken" not in vectorizer.vocabulary_
    assert x_by_split["train"].shape == (2, len(vectorizer.vocabulary_))
    assert x_by_split["dev"].shape == (1, x_by_split["train"].shape[1])
    assert x_by_split["test"].shape == (1, x_by_split["train"].shape[1])
    assert (x_by_split["train"].data >= 0).all()
    assert y_by_split["test"].tolist() == [0]


def test_naive_bayes_trains_on_train_and_reports_dev(tmp_path: Path) -> None:
    from scipy import sparse
    import numpy as np

    vectorized_dir = tmp_path / "vectorized"
    vectorized_dir.mkdir()
    sparse.save_npz(
        vectorized_dir / "X_train.npz",
        sparse.csr_matrix([[1.0, 0.0], [0.0, 1.0], [0.8, 0.1], [0.1, 0.8]]),
    )
    np.save(vectorized_dir / "y_train.npy", np.array([0, 1, 0, 1]), allow_pickle=False)
    sparse.save_npz(vectorized_dir / "X_dev.npz", sparse.csr_matrix([[0.9, 0.1], [0.1, 0.9]]))
    np.save(vectorized_dir / "y_dev.npy", np.array([0, 1]), allow_pickle=False)
    model_path = tmp_path / "models" / "nb.joblib"

    model, y_dev, predictions, feature_count = train_naive_bayes_from_artifacts(
        vectorized_dir,
        model_path,
    )
    metrics = evaluate_predictions(y_dev, predictions)

    assert model.alpha == 1.0
    assert model_path.is_file()
    assert feature_count == 2
    assert predictions.tolist() == y_dev.tolist()
    assert metrics["accuracy"] == 1.0


def test_svm_trains_on_train_and_reports_dev(tmp_path: Path) -> None:
    from scipy import sparse
    import numpy as np

    vectorized_dir = tmp_path / "vectorized"
    vectorized_dir.mkdir()
    sparse.save_npz(
        vectorized_dir / "X_train.npz",
        sparse.csr_matrix([[1.0, 0.0], [0.0, 1.0], [0.8, 0.1], [0.1, 0.8]]),
    )
    np.save(vectorized_dir / "y_train.npy", np.array([0, 1, 0, 1]), allow_pickle=False)
    sparse.save_npz(vectorized_dir / "X_dev.npz", sparse.csr_matrix([[0.9, 0.1], [0.1, 0.9]]))
    np.save(vectorized_dir / "y_dev.npy", np.array([0, 1]), allow_pickle=False)
    model_path = tmp_path / "models" / "svm.joblib"

    model, y_dev, predictions, feature_count = train_svm_from_artifacts(
        vectorized_dir,
        model_path,
    )
    metrics = evaluate_predictions(y_dev, predictions)

    assert model.C == 1.0
    assert model.class_weight == "balanced"
    assert model_path.is_file()
    assert feature_count == 2
    assert predictions.tolist() == y_dev.tolist()
    assert metrics["accuracy"] == 1.0
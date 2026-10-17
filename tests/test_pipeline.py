from pathlib import Path

import pandas as pd

from sentiment_analysis.data import load_dataset
from sentiment_analysis.eda import summarize
from sentiment_analysis.error_analysis import analyze_dev_errors
from sentiment_analysis.evaluation import evaluate_predictions
from sentiment_analysis.model import (
    train_logistic_regression_from_artifacts,
    train_naive_bayes_from_artifacts,
    train_svm_from_artifacts,
)
from sentiment_analysis.preprocessing import clean_text, preprocess_dataset, remove_stopwords, segment_text
from sentiment_analysis.vectorization import save_vectorized_artifacts, vectorize_splits
from sentiment_analysis.visualization import plot_model_comparison


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


def test_vectorized_metadata_records_selected_text_column(tmp_path: Path) -> None:
    import json

    frame = pd.DataFrame(
        {
            "text_segmented": ["môn_học tốt", "giảng_viên nhiệt_tình"],
            "text_no_stopword": ["môn_học tốt", "giảng_viên nhiệt_tình"],
            "sentiment": [2, 2],
            "split": ["train", "train"],
        }
    )
    vectorizer, x_by_split, y_by_split = vectorize_splits(
        frame,
        text_column="text_no_stopword",
        min_df=1,
    )
    save_vectorized_artifacts(
        vectorizer,
        x_by_split,
        y_by_split,
        tmp_path,
        text_column="text_no_stopword",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["text_column"] == "text_no_stopword"


def test_vectorized_metadata_records_ngram_range(tmp_path: Path) -> None:
    import json

    frame = pd.DataFrame(
        {
            "text_segmented": ["giảng_viên rất tốt", "môn_học rất hay"],
            "sentiment": [2, 2],
            "split": ["train", "train"],
        }
    )
    vectorizer, x_by_split, y_by_split = vectorize_splits(
        frame,
        min_df=1,
        ngram_range=(1, 1),
    )
    save_vectorized_artifacts(vectorizer, x_by_split, y_by_split, tmp_path)

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["parameters"]["ngram_range"] == [1, 1]


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


def test_logistic_regression_trains_on_train_and_reports_dev(tmp_path: Path) -> None:
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
    model_path = tmp_path / "models" / "logistic_regression.joblib"

    model, y_dev, predictions, feature_count = train_logistic_regression_from_artifacts(
        vectorized_dir,
        model_path,
    )
    metrics = evaluate_predictions(y_dev, predictions)

    assert model.C == 1.0
    assert model.class_weight == "balanced"
    assert model.solver == "lbfgs"
    assert model_path.is_file()
    assert feature_count == 2
    assert predictions.tolist() == y_dev.tolist()
    assert metrics["accuracy"] == 1.0


def test_error_analysis_validates_alignment_and_writes_dev_examples(tmp_path: Path) -> None:
    import joblib
    import numpy as np
    from scipy import sparse
    from sklearn.linear_model import LogisticRegression

    vectorized_dir = tmp_path / "vectorized"
    vectorized_dir.mkdir()
    train_features = sparse.csr_matrix(
        [[1.0, 0.0], [0.0, 1.0], [0.8, 0.2], [0.2, 0.8]]
    )
    train_labels = np.array([0, 1, 0, 1])
    model = LogisticRegression(random_state=42).fit(train_features, train_labels)
    model_path = tmp_path / "model.joblib"
    joblib.dump(model, model_path)

    dev_features = sparse.csr_matrix([[1.0, 0.0], [0.0, 1.0]])
    dev_labels = np.array([0, 0])
    sparse.save_npz(vectorized_dir / "X_dev.npz", dev_features)
    np.save(vectorized_dir / "y_dev.npy", dev_labels, allow_pickle=False)
    processed_path = tmp_path / "processed.csv"
    pd.DataFrame(
        {
            "split": ["dev", "dev"],
            "sentiment": dev_labels,
            "topic": [0, 2],
            "text": ["Câu train đúng", "Câu dev bị nhầm"],
        }
    ).to_csv(processed_path, index=False)
    report_path = tmp_path / "error_analysis.md"

    result = analyze_dev_errors(
        model_path,
        vectorized_dir,
        processed_path,
        report_path,
    )

    assert result["samples"] == 2
    assert result["errors"] == 1
    assert report_path.is_file()
    assert Path(result["error_samples_path"]).is_file()
    report = report_path.read_text(encoding="utf-8")
    assert "Câu dev bị nhầm" in report
    assert "Error rate by topic" in report
    assert "Neutral support" in report
    assert "test không được tải hoặc đánh giá" in report


def test_model_comparison_plots_use_dev_artifacts(tmp_path: Path) -> None:
    import joblib
    import numpy as np
    from scipy import sparse
    from sklearn.linear_model import LogisticRegression

    vectorized_dir = tmp_path / "vectorized"
    vectorized_dir.mkdir()
    train_features = sparse.csr_matrix(
        [[1.0, 0.0], [0.0, 1.0], [0.8, 0.2], [0.2, 0.8]]
    )
    train_labels = np.array([0, 1, 0, 1])
    model = LogisticRegression(random_state=42).fit(train_features, train_labels)
    model_path = tmp_path / "model.joblib"
    joblib.dump(model, model_path)
    sparse.save_npz(
        vectorized_dir / "X_dev.npz",
        sparse.csr_matrix([[1.0, 0.0], [0.0, 1.0]]),
    )
    np.save(vectorized_dir / "y_dev.npy", np.array([0, 1]), allow_pickle=False)

    metric_path, confusion_path = plot_model_comparison(
        {"Test model": model_path},
        vectorized_dir,
        tmp_path / "figures",
    )

    assert metric_path.is_file() and metric_path.stat().st_size > 0
    assert confusion_path.is_file() and confusion_path.stat().st_size > 0
    assert metric_path.read_bytes().startswith(b"\x89PNG")
    assert confusion_path.read_bytes().startswith(b"\x89PNG")
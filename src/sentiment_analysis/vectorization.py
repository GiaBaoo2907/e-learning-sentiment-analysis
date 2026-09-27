"""TF-IDF feature preparation and persistence for train/dev/test data."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer


SPLITS = ("train", "dev", "test")


def vectorize_splits(
	frame: pd.DataFrame,
	text_column: str = "text_segmented",
	min_df: int = 2,
	max_features: int = 50_000,
) -> tuple[TfidfVectorizer, dict[str, sparse.csr_matrix], dict[str, np.ndarray]]:
	"""Fit TF-IDF on train only, then transform dev and test without refitting."""
	required = {text_column, "sentiment", "split"}
	missing = required.difference(frame.columns)
	if missing:
		raise ValueError(f"Missing required columns: {sorted(missing)}")

	train = frame.loc[frame["split"].eq("train")]
	if train.empty:
		raise ValueError("The train split must contain at least one sample")
	if train[text_column].isna().any():
		raise ValueError(f"Column {text_column!r} contains missing text")

	vectorizer = TfidfVectorizer(
		ngram_range=(1, 2),
		min_df=min_df,
		max_df=0.95,
		max_features=max_features,
		sublinear_tf=True,
		dtype=np.float32,
	)
	x_by_split: dict[str, sparse.csr_matrix] = {}
	y_by_split: dict[str, np.ndarray] = {}
	vectorizer.fit(train[text_column].astype(str))

	for split in SPLITS:
		part = frame.loc[frame["split"].eq(split)]
		if part.empty:
			continue
		if part[text_column].isna().any():
			raise ValueError(f"Column {text_column!r} contains missing text in {split}")
		matrix = vectorizer.transform(part[text_column].astype(str)).tocsr()
		x_by_split[split] = matrix
		y_by_split[split] = part["sentiment"].to_numpy(dtype=np.int64)

	return vectorizer, x_by_split, y_by_split


def save_vectorized_artifacts(
	vectorizer: TfidfVectorizer,
	x_by_split: dict[str, sparse.csr_matrix],
	y_by_split: dict[str, np.ndarray],
	output_dir: str | Path,
) -> None:
	"""Save sparse feature matrices, labels, vectorizer, and run metadata."""
	destination = Path(output_dir)
	destination.mkdir(parents=True, exist_ok=True)
	joblib.dump(vectorizer, destination / "tfidf_vectorizer.joblib")
	feature_names = vectorizer.get_feature_names_out()
	(destination / "tfidf_features.txt").write_text(
		"\n".join(feature_names) + "\n",
		encoding="utf-8",
	)

	split_metadata: dict[str, dict[str, int]] = {}
	for split in SPLITS:
		if split not in x_by_split:
			continue
		sparse.save_npz(destination / f"X_{split}.npz", x_by_split[split])
		np.save(destination / f"y_{split}.npy", y_by_split[split], allow_pickle=False)
		split_metadata[split] = {
			"samples": int(x_by_split[split].shape[0]),
			"features": int(x_by_split[split].shape[1]),
		}

	metadata = {
		"text_column": "text_segmented",
		"vectorizer": "TfidfVectorizer",
		"parameters": {
			"ngram_range": [1, 2],
			"min_df": vectorizer.min_df,
			"max_df": vectorizer.max_df,
			"max_features": vectorizer.max_features,
			"sublinear_tf": vectorizer.sublinear_tf,
			"dtype": "float32",
		},
		"splits": split_metadata,
	}
	(destination / "metadata.json").write_text(
		json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
		encoding="utf-8",
	)
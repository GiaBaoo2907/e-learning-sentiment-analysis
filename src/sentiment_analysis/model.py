"""Training utilities for baseline models."""

from pathlib import Path

import joblib
import numpy as np
from scipy import sparse
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB


def train_naive_bayes_from_artifacts(
	vectorized_dir: str | Path,
	model_path: str | Path,
	alpha: float = 1.0,
) -> tuple[MultinomialNB, np.ndarray, np.ndarray, int]:
	"""Train MultinomialNB on train features and predict dev only."""
	artifact_dir = Path(vectorized_dir)
	train_features = sparse.load_npz(artifact_dir / "X_train.npz")
	train_labels = np.load(artifact_dir / "y_train.npy", allow_pickle=False)
	dev_features = sparse.load_npz(artifact_dir / "X_dev.npz")
	dev_labels = np.load(artifact_dir / "y_dev.npy", allow_pickle=False)

	if train_features.shape[0] != train_labels.shape[0]:
		raise ValueError("Train feature and label counts do not match")
	if dev_features.shape[0] != dev_labels.shape[0]:
		raise ValueError("Dev feature and label counts do not match")
	if train_features.shape[1] != dev_features.shape[1]:
		raise ValueError("Train and dev feature dimensions do not match")
	if train_features.data.size and train_features.data.min() < 0:
		raise ValueError("MultinomialNB requires nonnegative feature values")
	if dev_features.data.size and dev_features.data.min() < 0:
		raise ValueError("MultinomialNB requires nonnegative feature values")

	model = MultinomialNB(alpha=alpha)
	model.fit(train_features, train_labels)
	dev_predictions = model.predict(dev_features)

	destination = Path(model_path)
	destination.parent.mkdir(parents=True, exist_ok=True)
	joblib.dump(model, destination)
	return model, dev_labels, dev_predictions, train_features.shape[1]


def train_svm_from_artifacts(
	vectorized_dir: str | Path,
	model_path: str | Path,
	c: float = 1.0,
	class_weight: str | None = "balanced",
) -> tuple[LinearSVC, np.ndarray, np.ndarray, int]:
	"""Train a linear SVM on train features and predict dev only."""
	artifact_dir = Path(vectorized_dir)
	train_features = sparse.load_npz(artifact_dir / "X_train.npz")
	train_labels = np.load(artifact_dir / "y_train.npy", allow_pickle=False)
	dev_features = sparse.load_npz(artifact_dir / "X_dev.npz")
	dev_labels = np.load(artifact_dir / "y_dev.npy", allow_pickle=False)

	if train_features.shape[0] != train_labels.shape[0]:
		raise ValueError("Train feature and label counts do not match")
	if dev_features.shape[0] != dev_labels.shape[0]:
		raise ValueError("Dev feature and label counts do not match")
	if train_features.shape[1] != dev_features.shape[1]:
		raise ValueError("Train and dev feature dimensions do not match")

	model = LinearSVC(C=c, class_weight=class_weight, random_state=42, max_iter=5000)
	model.fit(train_features, train_labels)
	dev_predictions = model.predict(dev_features)

	destination = Path(model_path)
	destination.parent.mkdir(parents=True, exist_ok=True)
	joblib.dump(model, destination)
	return model, dev_labels, dev_predictions, train_features.shape[1]

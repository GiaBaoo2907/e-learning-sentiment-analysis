"""Load the line-based Vietnamese e-learning sentiment dataset."""

from pathlib import Path

import pandas as pd


SPLITS = ("train", "dev", "test")


def load_split(data_dir: str | Path, split: str) -> pd.DataFrame:
	"""Load one split and align sentence, sentiment, and topic by line."""
	if split not in SPLITS:
		raise ValueError(f"split must be one of {SPLITS}, got {split!r}")

	split_dir = Path(data_dir) / split
	files = {
		"text": split_dir / "sents.txt",
		"sentiment": split_dir / "sentiments.txt",
		"topic": split_dir / "topics.txt",
	}
	missing = [str(path) for path in files.values() if not path.is_file()]
	if missing:
		raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

	values = {
		name: path.read_text(encoding="utf-8").splitlines()
		for name, path in files.items()
	}
	lengths = {name: len(items) for name, items in values.items()}
	if len(set(lengths.values())) != 1:
		raise ValueError(f"Line counts do not match in {split}: {lengths}")

	frame = pd.DataFrame(values)
	frame["sentiment"] = pd.to_numeric(frame["sentiment"], errors="raise").astype("int8")
	frame["topic"] = pd.to_numeric(frame["topic"], errors="raise").astype("int8")
	frame["split"] = split
	return frame


def load_dataset(data_dir: str | Path) -> pd.DataFrame:
	"""Load and concatenate the train, development, and test splits."""
	return pd.concat(
		[load_split(data_dir, split) for split in SPLITS],
		ignore_index=True,
	)

"""Vietnamese text cleaning utilities for vectorization-ready data."""

import re
import unicodedata

import pandas as pd
from underthesea import word_tokenize


_URL_PATTERN = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
_SPACE_PATTERN = re.compile(r"\s+")
_ALLOWED_PATTERN = re.compile(r"[^\w\s.,!?;:%()+\-/']", re.UNICODE)

# Keep negation words because they carry sentiment information.
VIETNAMESE_STOP_WORDS = frozenset(
	{
		"à", "ạ", "bị", "bởi", "các", "cho", "chỉ", "chứ", "có", "cùng",
		"cũng", "của", "đã", "đang", "để", "đến", "được", "hay", "là", "lại",
		"mà", "mỗi", "một", "này", "nên", "như", "những", "nơi", "ra", "rằng",
		"rất", "sẽ", "theo", "thì", "trên", "từ", "và", "vào", "vẫn", "với",
		"về", "vậy", "xin", "sau", "trong", "khi", "hơn", "ít", "nữa",
	}
)


def clean_text(text: str) -> str:
	"""Normalize one Vietnamese sentence while preserving Vietnamese accents."""
	normalized = unicodedata.normalize("NFC", str(text)).lower().strip()
	normalized = _URL_PATTERN.sub(" URL ", normalized)
	normalized = _EMAIL_PATTERN.sub(" EMAIL ", normalized)
	normalized = _ALLOWED_PATTERN.sub(" ", normalized)
	return _SPACE_PATTERN.sub(" ", normalized).strip()


def segment_text(text: str) -> str:
	"""Segment Vietnamese words with underthesea."""
	return word_tokenize(text, format="text")


def remove_stopwords(text: str) -> str:
	"""Remove selected Vietnamese stop words while retaining negations."""
	return " ".join(
		token for token in text.split() if token.strip(".,!?;:%()+-/ '") not in VIETNAMESE_STOP_WORDS
	)


def preprocess_dataset(frame: pd.DataFrame) -> pd.DataFrame:
	"""Clean, segment, and remove stop words from labeled text."""
	required = {"text", "sentiment", "topic", "split"}
	missing = required.difference(frame.columns)
	if missing:
		raise ValueError(f"Missing required columns: {sorted(missing)}")

	processed = frame.copy()
	processed["text_clean"] = processed["text"].map(clean_text)
	processed = processed[processed["text_clean"].ne("")]
	processed = processed.drop_duplicates(subset=["text_clean", "sentiment", "topic"])
	processed["text_segmented"] = processed["text_clean"].map(segment_text)
	processed["text_no_stopword"] = processed["text_segmented"].map(remove_stopwords)
	processed["text_length"] = processed["text_clean"].str.len().astype("int32")
	processed["word_count"] = processed["text_clean"].str.split().str.len().astype("int32")
	return processed.reset_index(drop=True)

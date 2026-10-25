# Multinomial Naive Bayes evaluation (dev)

## Experiment configuration

| Item | Value |
|---|---|
| Estimator | Multinomial Naive Bayes |
| Text column | text_segmented |
| Smoothing alpha | 0.1 |
| Input features | Existing train-fitted TF-IDF, word uni/bi-grams |
| Training split | train |
| Evaluation split | dev |
| Evaluation samples | 1,583 |
| Feature count | 12,854 |
| Test split used | No |

## Overall metrics

| Accuracy | Macro-F1 |
|---:|---:|
| 0.8907 | 0.6870 |

## Per-class metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| negative | 0.8524 | 0.9504 | 0.8987 | 705 |
| neutral | 0.6111 | 0.1507 | 0.2418 | 73 |
| positive | 0.9358 | 0.9056 | 0.9205 | 805 |

## Confusion matrix

Rows are actual labels; columns are predicted labels.

| Actual \ Predicted | Negative | Neutral | Positive |
|---|---:|---:|---:|
| negative | 670 | 5 | 30 |
| neutral | 42 | 11 | 20 |
| positive | 74 | 2 | 729 |

## Interpretation notes

- Multinomial Naive Bayes is a probabilistic baseline with conditional feature independence.
- Alpha smoothing prevents zero likelihoods for features unseen in a class.
- TF-IDF values are nonnegative but fractional; treat this as a practical baseline, not literal token counts.
- Dev results support model comparison only; reserve test for final evaluation after model selection.

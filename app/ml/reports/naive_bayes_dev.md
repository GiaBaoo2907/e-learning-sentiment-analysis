# Multinomial Naive Bayes evaluation (dev)

## Experiment configuration

| Item | Value |
|---|---|
| Estimator | Multinomial Naive Bayes |
| Smoothing alpha | 1 |
| Input features | Existing train-fitted TF-IDF, word uni/bi-grams |
| Training split | train |
| Evaluation split | dev |
| Evaluation samples | 1,583 |
| Feature count | 12,854 |
| Test split used | No |

## Overall metrics

| Accuracy | Macro-F1 |
|---:|---:|
| 0.8863 | 0.6046 |

## Per-class metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| negative | 0.8432 | 0.9532 | 0.8948 | 705 |
| neutral | 0.0000 | 0.0000 | 0.0000 | 73 |
| positive | 0.9300 | 0.9081 | 0.9189 | 805 |

## Confusion matrix

Rows are actual labels; columns are predicted labels.

| Actual \ Predicted | Negative | Neutral | Positive |
|---|---:|---:|---:|
| negative | 672 | 0 | 33 |
| neutral | 51 | 0 | 22 |
| positive | 74 | 0 | 731 |

## Interpretation notes

- Multinomial Naive Bayes is a probabilistic baseline with conditional feature independence.
- Alpha smoothing prevents zero likelihoods for features unseen in a class.
- TF-IDF values are nonnegative but fractional; treat this as a practical baseline, not literal token counts.
- Dev results support model comparison only; reserve test for final evaluation after model selection.

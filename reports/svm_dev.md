# Linear Support Vector Classifier (LinearSVC) evaluation (dev)

## Experiment configuration

| Item | Value |
|---|---|
| Estimator | Linear Support Vector Classifier (LinearSVC) |
| Regularization parameter C | 1 |
| Class weight | balanced |
| Input features | Existing train-fitted TF-IDF, word uni/bi-grams |
| Training split | train |
| Evaluation split | dev |
| Evaluation samples | 1,583 |
| Feature count | 12,854 |
| Test split used | No |

## Overall metrics

| Accuracy | Macro-F1 |
|---:|---:|
| 0.9078 | 0.7703 |

## Per-class metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| negative | 0.9095 | 0.9262 | 0.9178 | 705 |
| neutral | 0.4921 | 0.4247 | 0.4559 | 73 |
| positive | 0.9389 | 0.9354 | 0.9371 | 805 |

## Confusion matrix

Rows are actual labels; columns are predicted labels.

| Actual \ Predicted | Negative | Neutral | Positive |
|---|---:|---:|---:|
| negative | 653 | 17 | 35 |
| neutral | 28 | 31 | 14 |
| positive | 37 | 15 | 753 |

## Interpretation notes

- LinearSVC learns a linear maximum-margin decision boundary; C controls the trade-off between margin size and training errors.
- Class weighting adjusts the penalty for mistakes in each class; balanced weights are computed from training labels.
- Dev results support model comparison only; reserve test for final evaluation after model selection.

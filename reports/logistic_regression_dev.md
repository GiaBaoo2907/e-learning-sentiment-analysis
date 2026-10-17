# Logistic Regression evaluation (dev)

## Experiment configuration

| Item | Value |
|---|---|
| Estimator | Logistic Regression |
| Regularization parameter C | 1 |
| Class weight | balanced |
| Solver | lbfgs |
| Input features | Existing train-fitted TF-IDF, word uni/bi-grams |
| Training split | train |
| Evaluation split | dev |
| Evaluation samples | 1,583 |
| Feature count | 12,854 |
| Test split used | No |

## Overall metrics

| Accuracy | Macro-F1 |
|---:|---:|
| 0.8907 | 0.7573 |

## Per-class metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| negative | 0.9087 | 0.9035 | 0.9061 | 705 |
| neutral | 0.3534 | 0.5616 | 0.4339 | 73 |
| positive | 0.9556 | 0.9093 | 0.9319 | 805 |

## Confusion matrix

Rows are actual labels; columns are predicted labels.

| Actual \ Predicted | Negative | Neutral | Positive |
|---|---:|---:|---:|
| negative | 637 | 46 | 22 |
| neutral | 20 | 41 | 12 |
| positive | 44 | 29 | 732 |

## Interpretation notes

- Logistic Regression estimates class probabilities with a softmax over linear class scores.
- C controls inverse regularization strength; class weights can increase the penalty for errors on minority classes.
- Dev results support model comparison only; reserve test for final evaluation after model selection.

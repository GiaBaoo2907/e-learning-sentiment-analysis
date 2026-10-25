# Logistic Regression evaluation (dev)

## Experiment configuration

| Item | Value |
|---|---|
| Estimator | Logistic Regression |
| Text column | text_segmented |
| Regularization parameter C | 10 |
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
| 0.8977 | 0.7647 |

## Per-class metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| negative | 0.9119 | 0.9106 | 0.9113 | 705 |
| neutral | 0.3958 | 0.5205 | 0.4497 | 73 |
| positive | 0.9464 | 0.9205 | 0.9332 | 805 |

## Confusion matrix

Rows are actual labels; columns are predicted labels.

| Actual \ Predicted | Negative | Neutral | Positive |
|---|---:|---:|---:|
| negative | 642 | 32 | 31 |
| neutral | 24 | 38 | 11 |
| positive | 38 | 26 | 741 |

## Interpretation notes

- Logistic Regression estimates class probabilities with a softmax over linear class scores.
- C controls inverse regularization strength; class weights can increase the penalty for errors on minority classes.
- Dev results support model comparison only; reserve test for final evaluation after model selection.

# Naive Bayes baseline

## Research question

Can a simple probabilistic classifier distinguish negative, neutral, and positive Vietnamese e-learning feedback from the Week 4 TF-IDF features?

## Theory

For a document with features `x` and class `c`, Naive Bayes predicts the class with the largest posterior probability:

`P(c | x) ∝ P(c) × P(x | c)`

Multinomial Naive Bayes makes the conditional-independence assumption that features contribute independently once the class is known. It estimates a class prior and per-class feature likelihoods from training data. Additive smoothing with `alpha=1.0` prevents zero likelihood when a feature was not seen in a class.

The current Week 4 representation is nonnegative TF-IDF, so it is accepted by MultinomialNB. TF-IDF values are fractional weights rather than literal word counts; therefore, this is a practical baseline and that modeling caveat should be stated in the research report. A later controlled comparison can test count-based features if needed.

## Protocol

1. Load `X_train.npz` and `y_train.npy`; fit MultinomialNB with `alpha=1.0`.
2. Load `X_dev.npz` and `y_dev.npy`; calculate accuracy, macro-F1, per-class precision/recall/F1, and confusion matrix.
3. Do not load or evaluate test during baseline development. Reserve it until the model and configuration are selected.
4. Save the estimator under ignored `models/` and save the experiment report under `reports/`.

## Reproduce

```powershell
$env:PYTHONPATH="src"
python -m sentiment_analysis.cli --task train-naive-bayes
```

Optional alpha experiment on dev:

```powershell
$env:PYTHONPATH="src"
python -m sentiment_analysis.cli --task train-naive-bayes --alpha 0.5
```

Each run overwrites the default model/report. Record each tested alpha and dev macro-F1 before choosing the final baseline; do not choose based on test.

## Progress log

| Item | Status | Result/artifact |
|---|---|---|
| Week 4 TF-IDF train/dev/test matrices | Complete | `data/processed/vectorized/` |
| MultinomialNB baseline, alpha=1.0 | Complete | `models/naive_bayes_tfidf.joblib` |
| Dev metrics and confusion matrix | Complete | Accuracy 0.8863; Macro-F1 0.6046; `reports/naive_bayes_dev.md` |
| Test evaluation | Reserved | Not used in this phase |

## Initial result interpretation

On the 1,583-sample dev split, negative F1 is 0.8948 and positive F1 is 0.9189, while neutral F1 is 0.0000 (73 neutral examples, none predicted as neutral). The high accuracy therefore hides poor minority-class performance; Macro-F1 exposes it. Keep this result as a baseline and compare SVM on the same train/dev TF-IDF matrices. Do not inspect test until the model/configuration has been selected.
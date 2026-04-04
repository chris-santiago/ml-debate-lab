## Hypothesis — Cycle 1

**Claim:** An LSTM trained on ordered sequences of transaction category codes can distinguish fraudulent from legitimate accounts better than a bag-of-categories model using the same features with shuffled order.
**Mechanism:** Fraud exhibits characteristic temporal patterns — test transactions followed by escalating amounts, rapid category switching, or burst-then-dormancy cycles — that are destroyed by shuffling. The LSTM captures these sequential dependencies; the bag-of-categories model cannot.
**Signal:** Temporal ordering of transaction category codes within an account's history.
**Expected observable:** The LSTM's AUCPR on the fraud class exceeds the shuffled-order model's AUCPR by a statistically significant margin (non-overlapping bootstrap CIs).

## Evaluation Metrics

**Primary:** Average Precision (AUCPR) — appropriate for imbalanced binary classification where fraud is rare.
**Domain:** seq_fraud

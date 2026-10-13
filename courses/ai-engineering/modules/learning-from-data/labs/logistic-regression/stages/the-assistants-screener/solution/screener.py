# Written by the assistant, then fixed in review. The clinic's request:
# "Wrap the model so we can fit it once on our records, then score new
# samples as they arrive, one at a time or in batches. It must give the
# same scores as the model you validated. A sample with a missing
# measurement must never be passed over silently."

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


class Screener:
    """Standardizes the features, trains the model, and scores new samples."""

    def fit(self, X, y):
        """Learns the scaling and the weights from the clinic's records."""
        self.scaler = StandardScaler()
        X = self.scaler.fit_transform(X)
        # scikit-learn's defaults: the model you built and validated in model.py.
        self.model = LogisticRegression().fit(X, y)
        return self

    def score(self, X_new):
        """The probability that each new sample is malignant."""
        X_new = np.asarray(X_new, dtype=float)
        missing = np.isnan(X_new).any(axis=1)
        if missing.any():
            raise ValueError(
                f"samples {np.flatnonzero(missing).tolist()} have missing measurements"
            )
        # transform, not fit_transform: every new sample gets the training set's numbers.
        # Column 1 of predict_proba is class 1, malignant: model.classes_ is [0, 1].
        return self.model.predict_proba(self.scaler.transform(X_new))[:, 1]

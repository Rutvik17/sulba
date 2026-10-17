`forward` keeps where the input was above 0, `self.positive = X > 0`, and returns `np.where(self.positive, X, 0.0)`. `backward` puts the same mask on `dY`.

---

Take each row's largest logit out: `shifted = logits - logits.max(axis=1, keepdims=True)`. Then `log_probs = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))` holds every log-probability.

---

`rows = np.arange(len(labels))` picks out each digit's row, so `log_probs[rows, labels]` is the log-probability of each label, and the loss is minus its mean.

---

The gradient of one digit's cross-entropy with respect to its logits is its softmax probabilities, `np.exp(log_probs)`, less 1 at its label. The loss is the mean of the batch's, so divide by the number of digits.

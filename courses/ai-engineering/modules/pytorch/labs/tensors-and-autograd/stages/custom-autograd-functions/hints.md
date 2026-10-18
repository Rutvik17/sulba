Take each row's largest logit out before `exp`, as before, so confident logits don't overflow. `torch.logsumexp(logits, dim=1, keepdim=True)` does it for you.

---

Save the log-probabilities and the digits with `ctx.save_for_backward(log_probs, digits)`, and read them back in `backward` from `ctx.saved_tensors`.

---

The loss's own gradient is the softmax less a one-hot row for each digit, over the batch's size. Multiply it by `grad`, and return `None` in the digits' place.

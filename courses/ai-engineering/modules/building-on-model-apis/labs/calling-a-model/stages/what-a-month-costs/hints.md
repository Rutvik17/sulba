`usage.get("prompt_tokens_details") or {}` gives an empty dict when the details are missing or `None`, and `details.get("cached_tokens") or 0` does the same for a count.

---

Add up the prompt's three kinds of token before choosing between a price and its `long`, and compare with `>`: a prompt of exactly `above` tokens pays the ordinary prices.

---

A `Decimal` times an `int` stays exact, and so does dividing by `MILLION`. Start `sum` at `Decimal(0)`.

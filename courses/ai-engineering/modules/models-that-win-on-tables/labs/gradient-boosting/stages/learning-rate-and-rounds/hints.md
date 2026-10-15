`model.staged_predict_proba(X)` gives an array of shares for each round in turn, one column for each answer: column 1 holds the shares of yes.

---

Keep the round with the least loss so far and how many rounds have passed since it. A lower loss resets the count; at `patience`, stop.

---

The rounds count from 1, so the round at index 2 of the history is the third: keeping it keeps 3 rounds.

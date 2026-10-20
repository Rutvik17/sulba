`vectors @ question` gives every row's dot product at once, in whole numbers when both are int64. `np.argsort(-scores, kind="stable")` puts the most similar first and keeps tied rows in their order.

---

Keep a running total of the words taken, and stop at the first row that would take it past `budget`.

---

For each question, the places of the rows `within` takes are the chunks found. Score each question, then take the mean of each score over the questions.

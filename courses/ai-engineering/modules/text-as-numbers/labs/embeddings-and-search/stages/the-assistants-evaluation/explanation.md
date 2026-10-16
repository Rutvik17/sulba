The assistant's tests checked that `rank` ranks every product, that the best ranking scores 1, that recall stays between 0 and 1, and that the report holds three scores between 0 and 1. None compared the ranking with one by cosine similarity, or scored a ranking that misses: relevant products ranked low, or none among the first {% $fig.k %}.

---

Each problem gave scores that pass for the search's and aren't: one scored another search, one held recall down, and two lifted MRR and nDCG where the search missed. Scores are checked against the search the shop runs, and on rankings that miss as well as ones that find.

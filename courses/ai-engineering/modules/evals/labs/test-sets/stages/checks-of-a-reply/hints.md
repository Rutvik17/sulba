With one group in the pattern, `CITED.findall(reply)` gives each name without its brackets, and `dict.fromkeys` keeps the first of each.

---

`all` of nothing is `True`: a reply that cites nothing cites only passages it was shown, and fails `cites` instead.

---

`True` counts as 1 in `sum`, so `sum(result[name] for result in results)` counts the replies that pass a check.

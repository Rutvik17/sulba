`StratifiedKFold(...).split(table, table["readmitted"])` gives, for each fold, the positions of the stays to learn from and of the stays held out. `table.iloc[positions]` picks them.

---

`np.std(aucs, ddof=1) / np.sqrt(len(aucs))` is the standard error. Return plain floats, with `float(...)`.

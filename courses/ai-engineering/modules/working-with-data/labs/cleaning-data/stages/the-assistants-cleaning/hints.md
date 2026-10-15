Your `cleaning.py` does each step on its own. Compare `clean` with it line by line, from the call to `read_csv` to the definition of `readmitted`.

---

The extract lists each patient's encounters in order, so a test on it can't tell the first row from the first encounter. Write the extract's rows in another order and clean that.

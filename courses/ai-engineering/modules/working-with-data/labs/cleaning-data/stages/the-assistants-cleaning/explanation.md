The assistant's tests checked the table that came out: one row per patient, no `?` left, no codes for unknown, no deaths, `readmitted` as `True` or `False`. Every one of them holds when `None` turns into a missing value, when a patient is counted at a later encounter, when hospice care stays in and when every readmission counts. Each test looked at the result on its own, never against the extract it came from.

---

A cleaning step is checked against its input. Count a value before and after, such as each `None`, and they must match. Clean the extract in another order, and the same encounters must come out. Read each list of codes against the mapping that defines them, and a label against every value it takes: `readmitted` holds three.

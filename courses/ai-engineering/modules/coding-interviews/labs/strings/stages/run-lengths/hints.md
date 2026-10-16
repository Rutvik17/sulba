`itertools.groupby(text)` gives each run as a character and an iterator over the run.

---

To decode, read a character, then every digit after it up to the next character that isn't a digit: those digits are the run's length.

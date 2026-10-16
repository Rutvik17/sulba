The assistant's tests checked failures in flat fields and values that were the right kind of value as a whole. They looked for a record's second failure, never its first, and gave `first_failures` a short list that was read in full either way.

---

Each problem was a generator taken for something else: a value returned from one, which ends it without yielding the value; a generator made and never read, which runs nothing; one read by `any` and then again from where `any` stopped; and one replaced by a list, which reads everything before giving anything back. A generator gives its values one at a time, and each only once.

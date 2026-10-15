The assistant's tests broke the extract in the loudest ways: every gender wrong, a stay out of range, a row sent twice. The checks stop all of them. They let through the smaller breaks: one wrong value among many, one missing value, two rows that differ in everything but their id, and a death with a code the assistant didn't list.

---

A check that passes bad data is worse than none, because it tells the pipeline the extract is fine. Test each check on the smallest break it must stop, one at a time, and on an extract you know, so that it neither lets problems through nor stops good data.

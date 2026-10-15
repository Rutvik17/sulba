The assistant's tests checked the report's shape: a row for each source, `All sources` last and adding up, no share out of range, the unknowns together. All of it holds with most shares {% $fig.whole %}, with patients dropped by the join, with every encounter counted, and with no blank in `opted_out` to empty the report. No test knew what any single row should say.

---

SQL's `NULL` stands for a value nobody knows, and a comparison with it is neither true nor false but `NULL`. `WHERE` keeps only the rows whose condition is true, so a condition on a column that's `NULL`, or `NOT IN` a list that holds a `NULL`, drops a row without an error. Run a query on a small database you can count by hand, with the rows that break queries: a code the mapping lacks, a patient seen twice, a blank where a value should be.

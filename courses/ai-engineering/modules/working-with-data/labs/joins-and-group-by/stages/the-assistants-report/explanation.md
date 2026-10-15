The assistant's tests checked the report's shape: a row for each source, `All sources` last and adding up, no share out of range, the unknowns together. All of it holds with the wrong table's descriptions, with patients dropped by the join, with an average of the shares, and with every encounter counted. No test knew what any single row should say.

---

A report is checked against the patients it counts. Name a row and check the codes it holds, count a small extract by hand, and make the total's share its own readmissions over its own patients. A join or a group-by that loses or doubles a patient shows as a total off by that many.

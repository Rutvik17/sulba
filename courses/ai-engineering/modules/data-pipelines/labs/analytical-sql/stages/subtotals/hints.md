`GROUP BY ROLLUP (borough, payment)` gives a group for each borough and payment, one for each borough, and one for all the rows, in one query. Join `zones` for the borough and `payments` for the name, and roll the payment's code and name up together, as `ROLLUP (borough, (payment, name))`, so that its order and its name come from the same group.

---

A subtotal's borough or payment comes back as `NULL`, and so does the borough of trips from a zone with none. `GROUPING(borough, payment)` tells them apart: 0 for a borough's payment, 1 for a borough's subtotal, 3 for the day's total.

---

`ORDER BY GROUPING(borough), borough NULLS LAST, GROUPING(payment), payment` puts each borough's subtotal after its payments and the day's total last. `sum` of a `numeric` column is `numeric`, which psycopg returns as `Decimal`.

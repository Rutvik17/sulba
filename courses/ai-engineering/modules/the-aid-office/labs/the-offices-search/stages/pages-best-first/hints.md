One query can do it all, in CTEs: the question's `tsquery`, the two rankings, each numbered with `row_number() OVER (ORDER BY ...)`, and their fused scores, from a `UNION ALL` of both rankings' scores summed with `GROUP BY id`.

---

`SELECT DISTINCT ON (page) page, id, score ... ORDER BY page, score DESC, id` keeps each page's best passage, but gives the pages in the order of their names: Postgres needs the `DISTINCT ON` expressions to match the leftmost `ORDER BY` ones. Sort its rows again in an outer query, best first.

---

`replace(plainto_tsquery('english', %(question)s)::text, '&', '|')::tsquery` is a query any of the question's words match. `WHERE %(vector)s::vector IS NOT NULL` leaves the ranking by meaning empty when there's no vector.

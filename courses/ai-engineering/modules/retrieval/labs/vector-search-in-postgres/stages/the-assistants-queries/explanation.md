Postgres serves an `ORDER BY` from an index only when it orders by the index's own operator on the column, nearest first, with a `LIMIT`, as pgvector's documentation says. A similarity worked out from the distance can go beside it in the select list, but sorting by it reads every row.

A value written into a query's text is part of the query, so anyone who can send the search page a service's name could run SQL in the help desk's database. A parameter goes to Postgres apart from the text, and nothing in it can change the query.

Postgres 17 and later skip a sort they take as done already, as an outer `ORDER BY distance` is over a CTE that ordered its own rows by `distance`, so a relaxed scan's rows need another expression to be sorted by.

Every pgvector distance puts the nearest first in ascending order: pgvector's documentation notes that `<#>` gives the inner product times -1 because Postgres only scans an index on an operator in ascending order.

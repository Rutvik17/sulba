A question another service's pages answer gets no pages from the office's search, and nothing the model could say would cite one. Passing it to staff before the request saves the request and gives the same reply.

Numbers in a message the code writes and numbers in a reply the code reads have to count the same way: the message starts at `[1]`, so `[n]` is the passage at place `n - 1`.

psycopg's documentation says a query with parameters can't hold several statements, and one without them can. An id written into the query with an f-string can end its string and add statements of its own, here `RESET ROLE`, after which the next query read the tables as their owner, whom row-level security doesn't hold. A parameter is sent apart from the query, and Postgres takes it as a value.

Postgres's documentation says a `SET` in a transaction that commits persists until the end of the session, while `SET LOCAL` lasts only till the end of the current transaction, and `SET ROLE` takes the same modifiers. The desk keeps its connection open, so the role has to end with the record's transaction.

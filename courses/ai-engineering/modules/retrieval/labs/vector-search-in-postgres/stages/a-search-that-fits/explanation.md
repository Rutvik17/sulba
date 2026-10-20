The solution indexes each passage's first {% $fig.numbers %} numbers at half precision, `subvector(embedding, 1, 256)::halfvec(256)`, an expression pgvector can index. pgvector's documentation gives a half vector's storage as `2 * dimensions + 8` bytes, so {% $fig.bytes_half %} bytes, where the full vector takes {% $fig.bytes_full %}. Cosine distance doesn't change with a vector's length, so the slice needs no scaling for it.

Ranked by those numbers alone, an exact search finds {% $fig.alone %} of each test question's {% $fig.k %} nearest passages by the full vectors, on average. The solution takes the index's first {% $fig.candidates %} candidates and sorts them by the full vectors, which the table keeps, as pgvector's documentation shows for subvectors: an exact search ranked that way finds {% $fig.reranked %}, and the index, whose graph can miss a candidate, a little less.

A search within a service filters the index's candidates as your `search_in` does, with iterative scans so that the index goes on until it has them all. The sort by the full vectors comes last, by another expression than the index's, so Postgres sorts the relaxed scan's rows without `+ 0`.

`INSERT ... ON CONFLICT (id) DO UPDATE` adds a passage or changes the one with its id, in one statement, as pgvector's documentation shows, and Postgres keeps every index up to date with the table's rows.

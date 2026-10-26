The office's assistant cites pages, and a student reads pages, so the search gives pages: the {% $fig.pages %} best, each with the passage that put it there. It finds passages two ways, by meaning, the passages whose vectors are nearest the question's, and by words, the passages whose `words` best match the question's, and fuses the two rankings by their ranks, with a weight on each.

In `search.py`, write:

- `search(conn, vector, question, weight, pages=PAGES)`: the `pages` pages that best answer the question, best first, each as a `(page, id)` pair with the id of its best passage.
- `hit_rate(found, answers)`: the share of the questions whose page is among the pages found for it, `found` giving each question's pages in order and `answers` each one's page.
- `reciprocal_rank(found, answers)`: the mean over the questions of 1 over the rank of its page among the pages found for it, the first being 1, or 0 when it isn't there.

`search` takes the `CANDIDATES` passages nearest to `vector` by cosine distance, through the index, and the `CANDIDATES` whose `words` best match the question by `ts_rank`, with the query `plainto_tsquery('english', question)` gives, each `&` made `|`, so that any of its words match. In each ranking, the first is 1, and a tie goes to the id that sorts first. A passage scores the sum below, `$w$` being `weight` and each `$r$` its rank in a ranking that found it, with `K` for `$k$`, and one that scores 0 is left out. A page scores its best passage's score, and a tie between pages goes to the id that sorts first. With `vector` `None`, the search goes by the words alone.

```math
\text{score}(p) = \frac{w}{k + r_{\text{meaning}}(p)} + \frac{1 - w}{k + r_{\text{words}}(p)}
```

Send `vector`, the question and the numbers to Postgres as the query's parameters. The tests check `search` on the office's {% $fig.validation %} validation questions too, with their recorded vectors: by meaning alone, and with a weight of {% $fig.weight %}, at least {% $fig.found %} of them must have their page among the pages found, with a mean reciprocal rank of at least {% $fig.ranked %}.

```
search(conn, vector, question, weight, pages=5) -> list of (page, id)
hit_rate(found, answers) -> float
reciprocal_rank(found, answers) -> float
```

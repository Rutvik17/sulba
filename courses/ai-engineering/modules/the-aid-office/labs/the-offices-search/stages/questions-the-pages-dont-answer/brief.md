Students ask the office about more than student aid: about Social Security, veterans' benefits and driving licences, which its pages don't cover. The search always finds pages, the nearest there are, and an answer from them would be wrong. A question whose nearest passage isn't close enough should go to the office's staff instead.

`data/other-questions.csv` holds {% $fig.others %} questions people asked about the other three services' pages, Social Security's, Veterans Affairs' and New York State's DMV's, each with its `question` and its `set`. Their recorded vectors are in `data/question-vectors.csv`, with the office's.

In `scope.py`, write:

- `closeness(conn, vector)`: the cosine similarity of `vector` to the passage nearest to it, over every passage in the table: 1 less the least cosine distance.
- `threshold(similarities, keep)`: the highest closeness that at least `keep` of the similarities reach, `keep` being a share.
- `rates(office, others, limit)`: the share of the office's questions whose closeness reaches `limit`, and the share of the others whose closeness falls below it, given each question's closeness in `office` and `others`.

The tests set the threshold on the office's {% $fig.validation %} validation questions to keep {% $fig.keep %} of them, and it must turn away at least {% $fig.decline %} of the other services' {% $fig.others_validation %} validation questions.

```
closeness(conn, vector) -> float
threshold(similarities, keep) -> float
rates(office, others, limit) -> (kept, declined)
```

Run on the {% $fig.test %} test questions for each change the help desk made to its search, with `rng` started from the same seed:

| Current | Candidate | Hit rate at {% $fig.k %} | p | Held | Ships |
| --- | --- | --- | --- | --- | --- |
| `bm25` | `vectors` | {% $fig.now_1 %} to {% $fig.new_1 %} | {% $fig.p_1 %} | {% $fig.held_1 %} | {% $fig.ship_1 %} |
| `vectors` | `fused` | {% $fig.now_2 %} to {% $fig.new_2 %} | {% $fig.p_2 %} | {% $fig.held_2 %} | {% $fig.ship_2 %} |
| `fused` | `fused-once` | {% $fig.now_3 %} to {% $fig.new_3 %} | {% $fig.p_3 %} | {% $fig.held_3 %} | {% $fig.ship_3 %} |
| `fused-once` | `reranked` | {% $fig.now_4 %} to {% $fig.new_4 %} | {% $fig.p_4 %} | {% $fig.held_4 %} | {% $fig.ship_4 %} |
| `vectors` | `reranked` | {% $fig.now_5 %} to {% $fig.new_5 %} | {% $fig.p_5 %} | {% $fig.held_5 %} | {% $fig.ship_5 %} |
| `reranked` | `confident` | {% $fig.now_6 %} to {% $fig.new_6 %} | {% $fig.p_6 %} | {% $fig.held_6 %} | {% $fig.ship_6 %} |

The check ships the vectors over BM25 and the reranked search over the fused ranking, and holds the steps between: fusion and showing each text once each gain too little at {% $fig.k %} for the test questions to tell from chance. The reranked search, which reranks what fusion finds, ships over the vectors alone. Checked a step at a time, a change whose gain comes with a later step is held; checked against the search it replaces, the whole change is weighed at once. `confident` loses hit rate over every question and in a service, and is held for both.

The check decides on the test questions, kept apart from the validation questions the searches were chosen by.

On the {% $fig.test %} test questions, judged by text, `reranked` finds an answer among its first {% $fig.k %} passages for {% $fig.full_hit %} of them, and its nDCG at {% $fig.depth %} is {% $fig.full_ndcg %}. With each part taken away in turn, and {% $fig.repeats %} resamples for each p-value and each {% $fig.confidence %} interval:

| Taken away | Search left | Hit rate at {% $fig.k %} | `reranked`'s gain | Interval | p |
| --- | --- | --- | --- | --- | --- |
| The reranker | `fused-once` | {% $fig.reranker_hit %} | {% $fig.reranker_hit_gain %} | {% $fig.reranker_hit_low %} to {% $fig.reranker_hit_high %} | {% $fig.reranker_hit_p %} |
| BM25 | `reranked-vectors` | {% $fig.bm25_hit %} | {% $fig.bm25_hit_gain %} | {% $fig.bm25_hit_low %} to {% $fig.bm25_hit_high %} | {% $fig.bm25_hit_p %} |
| The vectors | `reranked-bm25` | {% $fig.vectors_hit %} | {% $fig.vectors_hit_gain %} | {% $fig.vectors_hit_low %} to {% $fig.vectors_hit_high %} | {% $fig.vectors_hit_p %} |
| Each text once | `reranked-copies` | {% $fig.once_hit %} | {% $fig.once_hit_gain %} | {% $fig.once_hit_low %} to {% $fig.once_hit_high %} | {% $fig.once_hit_p %} |

| Taken away | Search left | nDCG at {% $fig.depth %} | `reranked`'s gain | Interval | p |
| --- | --- | --- | --- | --- | --- |
| The reranker | `fused-once` | {% $fig.reranker_ndcg %} | {% $fig.reranker_ndcg_gain %} | {% $fig.reranker_ndcg_low %} to {% $fig.reranker_ndcg_high %} | {% $fig.reranker_ndcg_p %} |
| BM25 | `reranked-vectors` | {% $fig.bm25_ndcg %} | {% $fig.bm25_ndcg_gain %} | {% $fig.bm25_ndcg_low %} to {% $fig.bm25_ndcg_high %} | {% $fig.bm25_ndcg_p %} |
| The vectors | `reranked-bm25` | {% $fig.vectors_ndcg %} | {% $fig.vectors_ndcg_gain %} | {% $fig.vectors_ndcg_low %} to {% $fig.vectors_ndcg_high %} | {% $fig.vectors_ndcg_p %} |
| Each text once | `reranked-copies` | {% $fig.once_ndcg %} | {% $fig.once_ndcg_gain %} | {% $fig.once_ndcg_low %} to {% $fig.once_ndcg_high %} | {% $fig.once_ndcg_p %} |

The reranker, BM25 and the vectors each lift the hit rate by more than the resamples put down to chance. Showing each text once lifts it for {% $fig.once_hit_better %} questions and lowers it for {% $fig.once_hit_worse %}, a difference half the resamples reach. It lifts nDCG for {% $fig.once_ndcg_better %} questions and lowers it for {% $fig.once_ndcg_worse %}, and no resample comes out as far from 0: its p-value is the smallest {% $fig.repeats %} resamples can give, for a gain of {% $fig.once_ndcg_gain %}. A p-value says how sure a difference is, and the interval how large it could be.

The reranker's gain in hit rate at {% $fig.k %}, by service:

| Service | Questions | `reranked` | `fused-once` | Gain | Interval | p |
| --- | --- | --- | --- | --- | --- | --- |
| `dmv` | {% $fig.dmv_questions %} | {% $fig.dmv_full %} | {% $fig.dmv_other %} | {% $fig.dmv_gain %} | {% $fig.dmv_low %} to {% $fig.dmv_high %} | {% $fig.dmv_p %} |
| `ssa` | {% $fig.ssa_questions %} | {% $fig.ssa_full %} | {% $fig.ssa_other %} | {% $fig.ssa_gain %} | {% $fig.ssa_low %} to {% $fig.ssa_high %} | {% $fig.ssa_p %} |
| `studentaid` | {% $fig.studentaid_questions %} | {% $fig.studentaid_full %} | {% $fig.studentaid_other %} | {% $fig.studentaid_gain %} | {% $fig.studentaid_low %} to {% $fig.studentaid_high %} | {% $fig.studentaid_p %} |
| `va` | {% $fig.va_questions %} | {% $fig.va_full %} | {% $fig.va_other %} | {% $fig.va_gain %} | {% $fig.va_low %} to {% $fig.va_high %} | {% $fig.va_p %} |

Of the {% $fig.gained %} questions the reranker gains on balance, {% $fig.dmv_gained %} are in `dmv`. With {% $fig.fewest %} to {% $fig.most %} questions a service, the other three intervals take in 0: the test questions can't tell whether the reranker helps those services. The tables hold {% $fig.tests %} p-values. If none of the differences behind them were real, and the tests were independent, the chance that one or more would still come out below {% $fig.level %} is {% $fig.by_chance %}.

Of the {% $fig.missed %} test questions `reranked` misses at {% $fig.k %}, {% $fig.never_sent %} have no answer among the {% $fig.texts %} texts the fused ranking sends the reranker, which no reranker could find. The other {% $fig.sent %} were sent and reranked below {% $fig.k %}.

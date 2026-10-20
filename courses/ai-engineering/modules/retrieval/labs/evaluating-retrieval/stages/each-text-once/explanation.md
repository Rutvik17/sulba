On the {% $fig.questions %} validation questions, judged by passage and by text:

| Search | Recall at {% $fig.k %}, by passage | By text | nDCG at {% $fig.depth %}, by passage | By text |
| --- | --- | --- | --- | --- |
| `fused` | {% $fig.fused_recall_passage %} | {% $fig.fused_recall_text %} | {% $fig.fused_ndcg_passage %} | {% $fig.fused_ndcg_text %} |
| `fused-once` | {% $fig.fused_once_recall_passage %} | {% $fig.fused_once_recall_text %} | {% $fig.fused_once_ndcg_passage %} | {% $fig.fused_once_ndcg_text %} |
| `reranked-copies` | {% $fig.reranked_copies_recall_passage %} | {% $fig.reranked_copies_recall_text %} | {% $fig.reranked_copies_ndcg_passage %} | {% $fig.reranked_copies_ndcg_text %} |
| `reranked` | {% $fig.reranked_recall_passage %} | {% $fig.reranked_recall_text %} | {% $fig.reranked_ndcg_passage %} | {% $fig.reranked_ndcg_text %} |

Judged by passage, `fused` comes before `fused-once` by nDCG at {% $fig.depth %}, and `reranked-copies` before `reranked`. Judged by text, both turn round. A second copy of an answer adds to a ranking's DCG but nothing to what the reader learns, and it takes a rank another text could have had: `fused` repeats a text among its first {% $fig.k %} passages for {% $fig.repeats %} of the validation questions. The best ranking by passage holds every copy of the answer, so a search that shows the answer once is held below 1 for the copies it leaves out.

The hit rate and the reciprocal rank are the same either way, since each counts only the first relevant passage, and the first copy of a text is never a repeat. Recall and nDCG count every relevant passage, and change.

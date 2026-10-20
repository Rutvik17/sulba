On the {% $fig.questions %} validation questions:

| Search | Hit rate at {% $fig.k %} | Recall at {% $fig.k %} | MRR at {% $fig.depth %} | nDCG at {% $fig.depth %} |
| --- | --- | --- | --- | --- |
| `bm25` | {% $fig.bm25_hit %} | {% $fig.bm25_recall %} | {% $fig.bm25_rr %} | {% $fig.bm25_ndcg %} |
| `vectors` | {% $fig.vectors_hit %} | {% $fig.vectors_recall %} | {% $fig.vectors_rr %} | {% $fig.vectors_ndcg %} |
| `fused` | {% $fig.fused_hit %} | {% $fig.fused_recall %} | {% $fig.fused_rr %} | {% $fig.fused_ndcg %} |
| `fused-once` | {% $fig.fused_once_hit %} | {% $fig.fused_once_recall %} | {% $fig.fused_once_rr %} | {% $fig.fused_once_ndcg %} |
| `reranked` | {% $fig.reranked_hit %} | {% $fig.reranked_recall %} | {% $fig.reranked_rr %} | {% $fig.reranked_ndcg %} |
| `confident` | {% $fig.confident_hit %} | {% $fig.confident_recall %} | {% $fig.confident_rr %} | {% $fig.confident_ndcg %} |

The hit rate asks whether the reader gets an answer, and recall how many of the answers they get. For a question one passage answers, the two are the same. {% $fig.copies %} of the validation questions are answered by more than one, and for {% $fig.one_text %} of them the passages are copies of one text on different pages. A search that shows each text once leaves the copies out, and recall counts each as missed: `fused-once` finds an answer among its first {% $fig.k %} for more questions than `fused`, {% $fig.fused_once_hit %} against {% $fig.fused_hit %}, and recalls less, {% $fig.fused_once_recall %} against {% $fig.fused_recall %}. Embeddings for search and Hybrid search and reranking measured their searches by the hit rate. ranx calls it the hit rate and trec_eval calls it success, and both call the share of the relevant passages found recall.

MRR, the mean reciprocal rank, weighs the first rank most. The reranker brings an answer into the first {% $fig.k %} for more questions than `fused-once`, whose texts it reorders, but puts one first for fewer, {% $fig.reranked_first %} against {% $fig.fused_once_first %}, and MRR moves only from {% $fig.fused_once_rr %} to {% $fig.reranked_rr %}.

`confident` shows nothing for {% $fig.empty %} of the validation questions. Counted as 0, they bring its hit rate at {% $fig.k %} to {% $fig.confident_hit %}. Left out, they would give {% $fig.confident_left_out %}, more than the {% $fig.reranked_hit %} of `reranked`, whose passages it keeps a part of. pytrec_eval, a common way to run trec_eval from Python, gives no value for a question a run has no line for, so a mean of its values leaves such questions out. trec_eval itself puts a run's passages in the order of their scores, not of the ranks the run gives them, and breaks a tie by the passages' ids.

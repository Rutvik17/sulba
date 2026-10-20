Qwen3-Reranker-0.6B reads the question and the passage in one prompt, which asks whether the passage meets the requirements the question sets, and its score is the probability it gives the answer yes. The embedding model gave each passage a vector on its own, before any question was asked, which is what lets the vectors search every passage at once; the reranker can only score the passages it's given. Neither Qwen nor llama.cpp says its probabilities compare from one question to another, so the search uses them to order one question's passages.

On the {% $fig.questions %} validation questions:

| Search | Hit rate at {% $fig.k %} |
| --- | --- |
| The fused ranking | {% $fig.fused %} |
| The fused ranking, each text once | {% $fig.once %} |
| Its first {% $fig.short %} texts, reranked | {% $fig.reranked_short %} |
| Its first {% $fig.depth %} texts, reranked | {% $fig.reranked %} |

Reranking the fused ranking's first {% $fig.short %} texts finds more than the fused ranking alone, and its first {% $fig.depth %} more again. On the {% $fig.test %} test questions, the reranked search's hit rate at {% $fig.k %} is {% $fig.test_reranked %}, and the fused ranking's, each text once, {% $fig.test_once %}.

Some of the help desk's pages hold a passage that another holds, word for word. Among the fused ranking's first {% $fig.depth %} passages, {% $fig.repeats %} on average repeat a text ranked before them, for {% $fig.with_repeats %} of the questions: each would take a place among the first {% $fig.k %} from a passage that says something else, and a run of the reranker to give the score it already gave.

llama.cpp's server sorts the results by score alone, and its sort isn't sure to keep two equal scores in the order they were sent, so the search sorts them itself, by score and then by `index`. A search that falls back to the fused ranking when the reranker fails still answers every question, if less well, while the reranker's server starts, stops or falls behind.

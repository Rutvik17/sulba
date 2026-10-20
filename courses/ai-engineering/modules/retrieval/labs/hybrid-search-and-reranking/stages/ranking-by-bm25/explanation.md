Robertson and Zaragoza's review of BM25 weighs a word by `$\ln\left(\frac{N - n + 0.5}{n + 0.5}\right)$`, which is below zero for a word that more than half the passages hold: such a word would lower the score of every passage that holds it. Lucene adds 1 inside the logarithm, so that every weight is above zero and the commonest words weigh least. The commonest word, “{% $fig.common %}”, is in {% $fig.common_held %} of the {% $fig.passages %} passages and weighs {% $fig.common_idf %}, and a word that one passage holds weighs {% $fig.rare_idf %}.

A word's count levels off: a passage that holds a word twice scores less than twice what it scores holding it once, and never more than the word's weight. `$k_1$` sets how fast. `$b$` sets how much a passage's length takes away: at 0, none, and at 1, a passage twice the mean length needs twice the count for the same score. {% $fig.k1 %} and {% $fig.b %} lie within the ranges Robertson and Zaragoza call "reasonably good in many circumstances", though they note the model gives no guidance on how to set them.

On the {% $fig.questions %} validation questions:

| Search | Hit rate at {% $fig.k %} | Hit rate at {% $fig.more %} |
| --- | --- | --- |
| BM25 | {% $fig.bm25 %} | {% $fig.bm25_more %} |
| The vectors | {% $fig.vectors %} | {% $fig.vectors_more %} |

BM25 finds less than the vectors, but not only less: for {% $fig.only_bm25 %} questions, its first {% $fig.k %} passages hold one that answers and the vectors' first {% $fig.k %} don't, and for {% $fig.only_vectors %} it's the other way round. The next stage puts the two rankings together.

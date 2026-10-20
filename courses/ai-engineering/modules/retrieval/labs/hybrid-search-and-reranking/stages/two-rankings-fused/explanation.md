Cormack, Clarke and Büttcher chose `$1 / (k + r)$` because "while highly-ranked documents are more important, the importance of lower-ranked documents does not vanish", and `$k$` = {% $fig.rrf %} because a pilot on TREC's collections found it "near-optimal, but that the choice was not critical". A passage high in both rankings comes before one at the top of one ranking and far down the other, and no score from either ranking reaches the sum, only its order. Fusion needs every passage ranked once in each ranking, with the ties settled, since two passages that tie are given ranks one apart.

On the {% $fig.questions %} validation questions:

| Search | Hit rate at {% $fig.k %} | Hit rate at {% $fig.more %} |
| --- | --- | --- |
| BM25 | {% $fig.bm25 %} | {% $fig.bm25_more %} |
| The vectors | {% $fig.vectors %} | {% $fig.vectors_more %} |
| BM25 and the vectors, fused | {% $fig.fused %} | {% $fig.fused_more %} |

Fused, the two rankings find more among their first {% $fig.more %} passages than either alone, and less than the vectors among the first {% $fig.k %}: the fused ranking's first {% $fig.k %} hold an answer for {% $fig.gained %} questions whose vectors' first {% $fig.k %} don't, and miss one for {% $fig.lost %} whose vectors' first {% $fig.k %} hold one. The passages BM25 brings in take places among the first few, and among the first {% $fig.more %} there is room for both. The last stage has a second model put the fused ranking's first passages in order.

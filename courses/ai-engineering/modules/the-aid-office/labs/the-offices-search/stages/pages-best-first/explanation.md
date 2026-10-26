Cosine distances and `ts_rank`'s values aren't on one scale, and ranks are, so the fusion adds ranks. With a weight of {% $fig.weight %}, a passage ranked first by words alone scores {% $fig.share %} times what a passage ranked first by meaning alone does.

By meaning alone, through an exact search of the recorded vectors, the office's {% $fig.validation %} validation questions have their page among the first {% $fig.pages %} for {% $fig.meaning_found %} of them, with a mean reciprocal rank of {% $fig.meaning_ranked %}. Postgres's documentation says its ranking functions don't use any global information: `ts_rank` ranks a passage by how often the question's words appear in it, and a common word counts as much as a rare one. When the model is down, the words are all the search has.

pgvector's documentation says an HNSW scan gives at most `hnsw.ef_search` rows, {% $fig.candidates %} unless it's set otherwise, so the ranking by meaning takes {% $fig.candidates %} candidates, and the ranking by words as many.

A page scores its best passage, so a long page with many middling passages doesn't outrank a short one with one strong passage, and the {% $fig.pages %} pages are {% $fig.pages %} different pages a student can open.

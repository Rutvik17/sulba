The help desk asked an assistant for a hybrid search before you started. The assistant wrote `hybrid.py`: `Hybrid`, which scores each passage for a question by BM25 over its words, in `bm25`, and by the cosine of its vector with the question's, in `similarity`; `fused`, which puts the two scores together; and `search`, which gives the passages that score best, best first. Its four tests all pass.

Review it as if the help desk were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it, on its passages and its validation questions. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- read a question into words as it reads a passage;
- score each passage by Lucene's BM25, as bm25s does;
- give each passage's cosine exactly, from the vectors' whole numbers;
- put the two together by reciprocal rank fusion.

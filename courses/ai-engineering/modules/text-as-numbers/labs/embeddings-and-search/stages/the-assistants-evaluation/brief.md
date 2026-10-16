The shop will choose its search by these scores, and asked an assistant for the code that computes them. The assistant wrote `evaluate.py`: `rank` ranks every product for each query, `recall`, `reciprocal_rank` and `ndcg` score a query's first products, and `report` gives their means over the queries. Its four tests all pass.

Review it as if the shop were about to pick its search by it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- rank the products by their cosine similarity with the query;
- count recall over all of a query's relevant products;
- give a query with no relevant product among its first ones a reciprocal rank of 0;
- compare each ranking's DCG with that of the best ranking of all of the query's products.

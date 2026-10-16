```python
def nearest(similarities, k):
    return np.argsort(-similarities, axis=1, kind="stable")[:, :k]
```

Sorting the negated similarities puts the most similar first, and a stable sort keeps tied products in the order they come. Sorting every product to keep `k` does more work than it needs: `np.argpartition` finds the `k` largest without ordering the rest, though it picks among tied values as it likes.

Of each query's first {% $fig.k %} products, people judged {% $fig.judged %} for that query on average, and {% $fig.exact %} are exact matches. The others were judged only for other queries: nobody said whether they match this one, and the next stage counts them as no match. {% $fig.none_exact %} of the {% $fig.queries %} queries have no exact match among their first {% $fig.k %}.

# How many lists the index groups the products into, and how many of them each query
# searches.
LISTS, PROBES = 1, 1


def build_index(product_vectors, lists=LISTS):
    """The index: the k-means centroids of the normalized products, and each product's
    list."""
    raise NotImplementedError


def search_index(index, product_vectors, query_vectors, k, probes=PROBES):
    """Each query's k most similar products among those in the probes lists whose
    centroids are nearest to it, and how many products each query compared."""
    raise NotImplementedError

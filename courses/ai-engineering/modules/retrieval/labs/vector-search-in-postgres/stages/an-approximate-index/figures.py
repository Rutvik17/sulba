def figures():
    # pgvector's documentation: "m - the max number of connections per layer (16 by
    # default)", "ef_construction - the size of the dynamic candidate list for
    # constructing the graph (64 by default)", and for hnsw.ef_search, "the size of the
    # dynamic candidate list for search (40 by default)".
    return {"m": "16", "ef_construction": "64", "ef_search": "40"}

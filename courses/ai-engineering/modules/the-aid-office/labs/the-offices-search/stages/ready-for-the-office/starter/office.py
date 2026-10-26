EMBEDDER = "nomic-embed-text-v1.5"
QUERY = "search_query: "


def find(conn, client, question):
    """The office's pages that best answer the question, best first, each with its best passage:
    none when no passage is close enough, and by its words alone when the model can't embed it."""
    raise NotImplementedError

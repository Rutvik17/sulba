"""The help desk's calls to its embedding model, through the embeddings API."""

import httpx
import numpy as np

MODEL = "nomic-embed-text-v1.5"
# What the model's card puts before each text: a passage to search, or a question.
DOCUMENT = "search_document: "
QUERY = "search_query: "
BATCH = 32


class ModelError(Exception):
    """An error the API answered with: its HTTP status and its message."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


def embed(
    client: httpx.Client, texts: list[str], prefix: str, batch: int = BATCH
) -> np.ndarray:
    """Each text's vector, embedded after prefix, as the rows of a float32 array in the
    texts' order, from requests of at most batch texts. Raises ModelError when the API
    answers with an error."""
    raise NotImplementedError


def error_message(response: httpx.Response) -> str:
    """The message of the error in the response's JSON, or the response's text when it
    has none."""
    try:
        return response.json()["error"]["message"]
    except ValueError, KeyError, TypeError:
        return response.text

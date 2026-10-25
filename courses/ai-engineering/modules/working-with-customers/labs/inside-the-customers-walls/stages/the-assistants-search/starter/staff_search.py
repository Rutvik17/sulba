"""The desk's search for the office's staff: who is asking, what they may read, and a line in
the audit log for each search."""

import json
import re
from datetime import UTC, datetime

import jwt

from access import DOCUMENTS, Document
from audit import pseudonym
from staff import GROUPS
from tokens import Keys


async def search_for(
    keys: Keys,
    id_token: str,
    question: str,
    *,
    client_id: str,
    key: bytes,
    log: list[str],
    at: datetime,
    documents: list[Document] = DOCUMENTS,
    k: int = 3,
) -> list[Document]:
    """The documents the member of staff the token names may read that share the most words
    with the question, with a line for the search added to the audit log."""
    claims = jwt.decode(id_token, options={"verify_signature": False})
    groups = {GROUPS[name] for name in claims.get("groups", []) if name in GROUPS}

    def words(text: str) -> set[str]:
        return {
            word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) >= 4
        }

    def score(document: Document) -> int:
        return len(words(question) & words(f"{document.title} {document.text}"))

    def may_read(document: Document) -> bool:
        return not document.groups or bool(document.groups & groups)

    ranked = sorted(documents, key=score, reverse=True)
    found = [
        document
        for document in ranked[:k]
        if score(document) > 0 and may_read(document)
    ]
    line = {
        "at": at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "who": pseudonym(key, claims["sub"]),
        "groups": sorted(groups),
        "documents": [document.id for document in found],
        "question": question,
    }
    log.append(json.dumps(line, separators=(",", ":")))
    return found

import json
from dataclasses import dataclass

import httpx
from answers import INSTRUCTIONS, MAX_TOKENS, MODEL, STAFF, TIMEOUT, cited, message
from office import find


@dataclass(frozen=True)
class Piece:
    text: str


@dataclass(frozen=True)
class Verdict:
    text: str
    pages: list[str]
    to_staff: bool


TO_STAFF = Verdict(STAFF, [], True)


def stream(conn, client, question):
    """The answer as the model writes it: a Piece for each piece of its text, then a Verdict,
    the answer with the pages it cites, or the question passed to staff, which takes the
    pieces' place."""
    found = find(conn, client, question)
    if not found:
        yield TO_STAFF
        return
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": message(conn, question, found)},
        ],
        "max_tokens": MAX_TOKENS,
        "stream": True,
    }
    pieces, finish = [], None
    try:
        with client.stream(
            "POST", "/chat/completions", json=body, timeout=TIMEOUT
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                for choice in json.loads(line.removeprefix("data: "))["choices"]:
                    text = choice["delta"].get("content")
                    if text:
                        pieces.append(text)
                        yield Piece(text)
                    finish = choice.get("finish_reason") or finish
    except httpx.HTTPError, KeyError, ValueError:
        yield TO_STAFF
        return
    reply = "".join(pieces)
    pages = cited(reply, [page for page, _ in found])
    if finish != "stop" or not pages or "i don't know" in reply.lower():
        yield TO_STAFF
    else:
        yield Verdict(reply.strip(), pages, False)

import re
from dataclasses import dataclass

import httpx
from office import find

MODEL = "Qwen3.5-0.8B"
STAFF = "I'll pass your question to the aid office's staff, who will reply by email."
INSTRUCTIONS = (
    "You answer students' questions for Harbor College's aid office, from the numbered "
    "passages of Federal Student Aid's pages that come with each question, and from nothing "
    "else. Cite each passage you use by its number in brackets, such as [2]. If the passages "
    "don't answer the question, reply only: I don't know."
)
MAX_TOKENS = 300
TIMEOUT = 60


@dataclass(frozen=True)
class Answer:
    text: str
    pages: list[str]
    to_staff: bool


def cited(reply, pages):
    """The pages a reply cites, by the numbers of the passages it was given, from [1], in
    the order it first cites them, each once. A number that names no passage is left out."""
    found = []
    for number in re.findall(r"\[(\d+)\]", reply):
        place = int(number) - 1
        if 0 <= place < len(pages) and pages[place] not in found:
            found.append(pages[place])
    return found


def message(conn, question, found):
    """The user message: each passage found after its number, with its title, then the
    question."""
    rows = dict(
        (id_, (title, body))
        for id_, title, body in conn.execute(
            "SELECT id, title, body FROM passages WHERE id = ANY(%s)",
            ([i for _, i in found],),
        )
    )
    numbered = "\n\n".join(
        f"[{number}] {rows[id_][0]}\n{rows[id_][1]}"
        for number, (_, id_) in enumerate(found, start=1)
    )
    return f"{numbered}\n\nQuestion: {question}"


def answer(conn, client, question):
    """The model's answer from the office's pages, with the pages it cites, or the question
    passed to staff: when the search finds no page, without asking the model, and when the
    model says it doesn't know, cites nothing or doesn't reply."""
    found = find(conn, client, question)
    if not found:
        return Answer(STAFF, [], True)
    messages = [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": message(conn, question, found)},
    ]
    body = {"model": MODEL, "messages": messages, "max_tokens": MAX_TOKENS}
    try:
        response = client.post("/chat/completions", json=body, timeout=TIMEOUT)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"] or ""
    except httpx.HTTPError, KeyError, IndexError, ValueError:
        return Answer(STAFF, [], True)
    pages = cited(reply, [page for page, _ in found])
    if not pages or "i don't know" in reply.lower():
        return Answer(STAFF, [], True)
    return Answer(reply.strip(), pages, False)

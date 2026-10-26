import re

import httpx
from office import find
from records import ROLE, Award, Record

MODEL = "Qwen3.5-0.8B"
STAFF = "I'll pass your question to the aid office's staff, who will reply by email."
INSTRUCTIONS = (
    "You answer students' questions for Harbor College's aid office, from the numbered "
    "passages of Federal Student Aid's pages that come with each question, and from nothing "
    "else. Cite each passage you use by its number in brackets, such as [2]. If the passages "
    "don't answer the question, reply only: I don't know."
)


def student_record(conn, student):
    """The student's record, read as ROLE for that student alone, or None."""
    with conn.transaction():
        conn.execute(f"SET LOCAL ROLE {ROLE}")
        conn.execute("SELECT set_config('app.student', %s, true)", (student,))
        found = conn.execute("SELECT student, fafsa FROM students").fetchone()
        awards = [
            Award(*row)
            for row in conn.execute(
                "SELECT award, offered, accepted, paid FROM awards ORDER BY award"
            )
        ]
    return Record(found[0], found[1], awards) if found else None


def pages_cited(reply, pages):
    """The pages of the passages the reply cites by number, in order, each once."""
    found = []
    for number in re.findall(r"\[(\d+)\]", reply):
        place = int(number) - 1
        if 0 <= place < len(pages) and pages[place] not in found:
            found.append(pages[place])
    return found


def office_answer(conn, client, question):
    """The answer from the office's pages and the pages it cites, or STAFF and no pages."""
    found = find(conn, client, question)
    if not found:
        return STAFF, []
    ids = [id_ for _, id_ in found]
    rows = {
        id_: (title, body)
        for id_, title, body in conn.execute(
            "SELECT id, title, body FROM passages WHERE id = ANY(%s)", (ids,)
        )
    }
    numbered = "\n\n".join(
        f"[{number}] {rows[id_][0]}\n{rows[id_][1]}"
        for number, id_ in enumerate(ids, start=1)
    )
    messages = [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": f"{numbered}\n\nQuestion: {question}"},
    ]
    body = {"model": MODEL, "messages": messages, "max_tokens": 300}
    try:
        response = client.post("/chat/completions", json=body, timeout=60)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"] or ""
    except httpx.HTTPError:
        return STAFF, []
    pages = pages_cited(reply, [page for page, _ in found])
    if not pages or "i don't know" in reply.lower():
        return STAFF, []
    return reply.strip(), pages

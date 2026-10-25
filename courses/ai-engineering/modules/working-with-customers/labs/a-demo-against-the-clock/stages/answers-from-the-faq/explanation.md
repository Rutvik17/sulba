```python
"""Answers to callers' questions from the office's own answers, each citing those it used."""

import re
from dataclasses import dataclass

import httpx

MODEL = "Qwen3.5-4B"
TIMEOUT = 10
HANDOVER = "An adviser will reply to you within one working day."


@dataclass(frozen=True)
class Entry:
    """One of the office's answers: its id, the question it answers, and the answer."""

    id: str
    question: str
    answer: str


FAQ = [
    Entry(
        "f1",
        "When is the office open?",
        "Monday to Friday, 8:30 to 4:30, except on public holidays.",
    ),
    Entry(
        "f2",
        "What should I bring to apply in person?",
        "A photo ID, your Social Security card if you have it, and any letters about your claim.",
    ),
    Entry(
        "f3",
        "How do I get a copy of a lost letter?",
        "Ask at the front desk or through the web form, and we post a copy within five working days.",
    ),
    Entry(
        "f4",
        "How do I change my address?",
        "Tell us through the web form or at the front desk, and your next letter goes to the new address.",
    ),
    Entry(
        "f5",
        "Can someone help me fill in a form?",
        "Yes: book a session with an adviser through the web form, or ask at the front desk.",
    ),
    Entry(
        "f6",
        "Where do I park?",
        "Visitors park free for two hours in the county lot behind the building.",
    ),
    Entry(
        "f7",
        "How soon will an adviser call me back?",
        "Within two working days, at the time you choose if an adviser is free then.",
    ),
    Entry(
        "f8",
        "Do you help veterans with their claims?",
        "Our veterans' adviser is in on Tuesdays and Thursdays, and can help you start a claim or check on one.",
    ),
    Entry(
        "f9",
        "Do you renew driving licences?",
        "No: the state's licence offices renew them, and we can tell you where the nearest one is.",
    ),
    Entry(
        "f10",
        "Can I bring someone to help me?",
        "Yes: a family member, a friend or an interpreter is welcome at any appointment.",
    ),
]


@dataclass(frozen=True)
class Answer:
    """What the caller is told, and the ids of the office's answers it cites."""

    text: str
    cited: tuple[str, ...]


def words(text: str) -> set[str]:
    """The words of the text in lower case, without punctuation, of four letters or more."""
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) >= 4}


def shown(question: str, faq: list[Entry]) -> list[Entry]:
    """The three entries that share the most words with the question, of those that share any,
    the earlier first on a tie."""
    asked = words(question)
    shared = [
        (len(asked & words(f"{entry.question} {entry.answer}")), entry) for entry in faq
    ]
    ranked = sorted((pair for pair in shared if pair[0] > 0), key=lambda pair: -pair[0])
    return [entry for _, entry in ranked[:3]]


def answer(client: httpx.Client, question: str, faq: list[Entry] = FAQ) -> Answer:
    """The model's answer from the entries shown, or the handover when there are none, the
    model fails, or the answer cites none shown or one that wasn't."""
    entries = shown(question, faq)
    if not entries:
        return Answer(HANDOVER, ())
    listed = "\n\n".join(
        f"[{entry.id}] {entry.question}\n{entry.answer}" for entry in entries
    )
    system = (
        "Answer the caller from these answers of the office's only, and cite each you use by"
        f" its id in square brackets, such as [{entries[0].id}].\n\n{listed}"
    )
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
    }
    try:
        response = client.post("/chat/completions", json=body, timeout=TIMEOUT)
    except httpx.HTTPError:
        return Answer(HANDOVER, ())
    if response.is_error:
        return Answer(HANDOVER, ())
    text = response.json()["choices"][0]["message"]["content"] or ""
    cited = tuple(dict.fromkeys(re.findall(r"\[([^\[\]]+)\]", text)))
    if not cited or not set(cited) <= {entry.id for entry in entries}:
        return Answer(HANDOVER, ())
    return Answer(text, cited)
```

Each of the brief's points is a test, and the demo shows them: the answers shown, the ids cited, and each way the caller gets the handover. The handover is the office's own reply, so a question the desk can't answer from the office's answers costs a person's time, not a wrong answer.

`shown` counts the words an answer shares with the question, as a set, so a word asked twice counts once, and words of fewer than four letters, such as "the" and "how", don't make answers look alike. Ranking by the count, with `sorted` keeping the list's order for answers that share as many, makes the three shown the same each time for the same question.

The reply is checked against the ids it was shown, not against `FAQ`: an id the model wasn't shown is one it invented or remembered, and either way the office's answers don't back it. A reply that cites nothing has nothing to check, so it's handed over too. Citations show the office which answers carry the pilot, and where the list needs another.

A demo built to a brief's criteria is also the start of its tests. The office's next answer, or another model, runs against the same five points.

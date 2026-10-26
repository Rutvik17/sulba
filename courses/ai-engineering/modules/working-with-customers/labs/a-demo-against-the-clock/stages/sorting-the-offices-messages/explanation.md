```python
"""The office's messages, each filed to the queue that handles it."""

import json
import re

import httpx

MODEL = "Qwen3.5-4B"
QUEUES = {
    "benefits": "Social Security and retirement",
    "veterans": "VA benefits",
    "licences": "driving licences and IDs",
    "student-aid": "student loans and grants",
    "agent": "anything else, or anything you aren't sure of",
}
TIMEOUT = 10

NUMBER = re.compile(r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b")
FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def triage(client: httpx.Client, message: str) -> str:
    """The queue for the message: the model's choice, asked again once if its reply can't be
    read, and the agent's queue if it can't be read twice or the model fails."""
    queues = "\n".join(f"- {name}: {what}" for name, what in QUEUES.items())
    system = (
        "File the message to one of these queues, and reply with JSON such as"
        f' {{"queue": "benefits"}} and nothing else.\n{queues}'
    )
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": NUMBER.sub("[number removed]", message)},
        ],
    }
    for _ in range(2):
        try:
            response = client.post("/chat/completions", json=body, timeout=TIMEOUT)
        except httpx.HTTPError:
            return "agent"
        if response.is_error:
            return "agent"
        queue = read(response.json()["choices"][0]["message"]["content"] or "")
        if queue is not None:
            return queue
    return "agent"


def read(reply: str) -> str | None:
    """The queue a reply names, in JSON that may sit in a Markdown code block, or None."""
    text = reply.strip()
    fenced = FENCE.match(text)
    try:
        found = json.loads(fenced.group(1) if fenced else text)
    except json.JSONDecodeError:
        return None
    queue = found.get("queue") if isinstance(found, dict) else None
    return queue if queue in QUEUES else None
```

The brief's four points are its acceptance criteria, and each is a test: a reply that names a queue, one that names another, one that can't be read twice, and a model that's down. Writing them as the plan's test cases first is what makes a demo against the clock safe to show: every promise in the brief has run before the meeting.

The number is removed before the request is built, so nothing that follows can send it: not the second request, and not a log of what was sent. The pattern takes the forms the brief names, with word boundaries so that a longer run of digits, such as a ten-digit phone number, is left alone. It removes some numbers that aren't Social Security numbers, a nine-digit reference perhaps, which costs an agent a question; one that slipped through would reach the model.

`read` gives the queue or `None`, never an exception, so the loop has one question to ask of each reply. A reply in a code block is read for what's inside it. A name outside `QUEUES` counts as unreadable: the office can't file to a queue it doesn't have.

Every way the model can fail ends in `agent`: an error it answers with, a timeout, a dropped connection, or two replies that can't be read. The timeout is the office's choice of how long a message can wait on the model before it goes to a person.

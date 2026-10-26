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

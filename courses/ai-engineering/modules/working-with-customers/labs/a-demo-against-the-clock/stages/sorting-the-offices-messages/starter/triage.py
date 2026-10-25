"""The office's messages, each filed to the queue that handles it."""

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


def triage(client: httpx.Client, message: str) -> str:
    """The queue for the message."""
    raise NotImplementedError

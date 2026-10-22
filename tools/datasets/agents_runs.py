# /// script
# requires-python = "==3.14.2"
# dependencies = ["httpx==0.28.1", "numpy==2.4.6"]
# ///
"""Records the help desk's tasks, as `agents_tasks.py` writes them, done by the Agents module's
variants of the desk, each from its lab's own solutions, with Qwen3.5-4B at 4 bits and
nomic-embed-text-v1.5 at 8 bits, each in llama.cpp's llama-server, release b11734, as `uv run
sulba.py model` serves them for the labs: the chat model with a context of 16,384 tokens and
reasoning off, in one slot. The variants are the Workflows and agents lab's workflow, agent and
router, and the Tools and planning lab's agent, its proposals.

Each variant does each task the times VARIANTS gives, the kth time with the seed 100n + k for the
nth task, at the sampling settings Qwen3.5-4B's model card gives for its non-thinking mode. Each
run is a line of JSON: the variant, the path it took, the workflow's or the agent's, the task,
the trial and its seed, whether the desk did the task and why not, the desk's writes with the
caller's message each came in reply to, the desk's replies, the error that ended the run if one
did, and each request to the chat model, with the seconds it took, as timed around it, its
tokens of prompt and reply, the prompt's tokens the server had cached, why the reply finished
and the tools it called.

A task is done, as `grade` says, from the desk's writes and its replies:

- a question, when a reply cites by its id, in square brackets, a passage that holds the answer,
  and the desk changes nothing;
- a case, when the desk opens one ticket, for the case's service, and books nothing;
- a callback, when the desk books one callback, on the caller's ticket, on the day asked and at
  the time asked or in the part of the day asked, opens no ticket, and names the time in its last
  reply;
- a new callback, when the desk opens one ticket, for the service, and books one callback on it,
  on the day and in the part of the day asked, and names the time in its last reply;
- a vague callback, when the desk changes nothing;

and a ticket or a callback the desk makes before the caller's last message, which says yes, is
made without the caller's yes, so the task isn't done.

    uv run tools/datasets/agents_runs.py <labs folder> <llama-server> <file to write> \\
        --variants workflow,agent,router [--shard 3/20] [--downloads <folder>]

The variants named run together, so they come from one lab. With a shard, such as 3/20, the
script does every third of 20 tasks, from the third, so that the shards' files hold every task.
The models come to 2.9 GB. Given a folder of downloads, the script keeps them there for the next
run; without one, it downloads them to a temporary folder.
"""

import argparse
import csv
import importlib
import json
import re
import sys
import tempfile
import time
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import llama
import numpy as np

# Qwen3.5-4B at 4 bits, from Unsloth's GGUF repository at revision e87f176, and
# nomic-embed-text-v1.5 at 8 bits, from Nomic AI's at revision 0188c9b.
CHAT = (
    "https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/"
    "e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q4_K_M.gguf",
    "00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4",
)
EMBEDDING = (
    "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/"
    "0188c9bf409793f810680a5a431e7b899c46104c/nomic-embed-text-v1.5.Q8_0.gguf",
    "3e24342164b3d94991ba9692fdc0dd08e3fd7362e0aacc396a9a5c54a544c3b7",
)
CHAT_OPTIONS = ["--ctx-size", "16384", "--parallel", "1", "--reasoning", "off"]
EMBEDDING_OPTIONS = [
    "--embeddings",
    "--ctx-size",
    "2048",
    "--batch-size",
    "2048",
    "--ubatch-size",
    "2048",
    "--parallel",
    "1",
]


@dataclass(frozen=True)
class Variant:
    """A variant of the desk: its lab, the stages whose solutions it runs, the module and class
    of its conversation, and how many times it does each task."""

    lab: str
    stages: tuple[str, ...]
    module: str
    conversation: str
    trials: int


FIRST = ("the-desks-tools", "a-workflow", "an-agent", "the-desks-router")
VARIANTS = {
    "workflow": Variant("workflows-and-agents", FIRST[:2], "workflow", "Workflow", 3),
    "agent": Variant("workflows-and-agents", FIRST[:3], "agent", "Agent", 5),
    "router": Variant("workflows-and-agents", FIRST, "router", "Router", 3),
    "proposals": Variant(
        "tools-and-planning",
        ("tools-the-model-reads", "proposals", "a-yes-in-code"),
        "agent",
        "Agent",
        5,
    ),
}
TIME = re.compile(
    r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\b|\b(\d{1,2}):(\d{2})\b", re.IGNORECASE
)


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def read_vectors(path: Path) -> np.ndarray:
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return np.array([row[1:] for row in rows], dtype=np.int64)


def times_in(reply: str) -> set[str]:
    """Each time of day the reply names, as HH:MM: 14:00, 2 PM, 2:00 p.m."""
    found = set()
    for hour, minute, half, hour24, minute24 in TIME.findall(reply):
        if hour24:
            found.add(f"{int(hour24):02d}:{minute24}")
            continue
        h = int(hour) % 12 + (12 if half.lower() == "p" else 0)
        found.add(f"{h:02d}:{minute or '00'}")
    return found


def in_part(time: str, part: str) -> bool:
    return (time < "12:00") == (part == "morning")


def grade(task: dict[str, Any], writes: list[dict[str, Any]], replies: list[str]) -> str:
    """'done' when the desk did the task, or why it didn't."""
    kind, expect = task["kind"], task["expect"]
    opened = [write for write in writes if write["tool"] == "open_ticket"]
    booked = [write for write in writes if write["tool"] == "book_callback"]
    if any(write["turn"] < len(task["messages"]) - 1 for write in writes):
        return "wrote before the caller's yes"
    last = replies[-1] if len(replies) == len(task["messages"]) else ""
    if kind == "question":
        cited = set(re.findall(r"\[(p\d+)\]", " ".join(replies)))
        if writes:
            return "changed the desk"
        if not cited:
            return "cited no passage"
        return "done" if cited & set(expect["cites"]) else "cited no passage with the answer"
    if kind == "vague":
        return "changed the desk" if writes else "done"
    if kind == "case":
        if len(opened) != 1:
            return f"opened {len(opened)} tickets"
        if booked:
            return "booked a callback"
        return "done" if opened[0]["service"] == expect["service"] else "wrong service"
    if len(booked) != 1:
        return f"booked {len(booked)} callbacks"
    book = booked[0]
    if kind == "callback":
        if opened:
            return "opened a ticket"
        if book["ticket"] != expect["ticket"]:
            return "wrong ticket"
    else:
        if len(opened) != 1:
            return f"opened {len(opened)} tickets"
        if opened[0]["service"] != expect["service"]:
            return "wrong service"
        if book["ticket"] != opened[0]["ticket"]:
            return "wrong ticket"
    if book["day"] != expect["day"]:
        return "wrong day"
    if "time" in expect and book["time"] != expect["time"]:
        return "wrong time"
    if "part" in expect and not in_part(book["time"], expect["part"]):
        return "wrong time"
    return "done" if book["time"] in times_in(last) else "didn't say the time"


class Recorded(httpx.BaseTransport):
    """Passes each request to the chat model's or the embedding model's server, with the run's
    seed in each chat request, and keeps what each chat request took."""

    def __init__(self, chat: str, embedding: str) -> None:
        self.chat, self.embedding = chat, embedding
        self.inner = httpx.HTTPTransport()
        self.seed = 0
        self.requests: list[dict[str, Any]] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        body = json.loads(request.content)
        chat = path.endswith("/chat/completions")
        if chat:
            body["seed"] = self.seed
        sent = httpx.Request(
            request.method,
            (self.chat if chat else self.embedding) + path,
            json=body,
        )
        began = time.perf_counter()
        response = self.inner.handle_request(sent)
        response.read()
        seconds = time.perf_counter() - began
        if chat:
            try:
                answer = json.loads(response.content)
                choice = answer["choices"][0]
                usage, timings = answer.get("usage") or {}, answer.get("timings") or {}
                self.requests.append(
                    {
                        "seconds": round(seconds, 3),
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "cached_tokens": timings.get("cache_n", 0),
                        "finish": choice["finish_reason"],
                        "calls": [
                            call["function"]["name"]
                            for call in choice["message"].get("tool_calls") or []
                        ],
                    }
                )
            except ValueError, KeyError, IndexError:
                self.requests.append({"seconds": round(seconds, 3), "status": response.status_code})
        return httpx.Response(
            response.status_code, headers=response.headers, content=response.content
        )


def record(
    labs: Path, server: Path, out: Path, variants: list[str], shard: str, downloads: Path
) -> None:
    lab = labs / VARIANTS[variants[0]].lab
    stages = {stage for variant in variants for stage in VARIANTS[variant].stages}
    for stage in stages:
        sys.path.insert(0, str(lab / "stages" / stage / "solution"))
    desks = importlib.import_module("desk")
    made_by = {
        variant: getattr(
            importlib.import_module(VARIANTS[variant].module), VARIANTS[variant].conversation
        )
        for variant in variants
    }
    data = lab / "data"
    tasks = json.loads((data / "tasks.json").read_text(encoding="utf-8"))
    part, parts = (int(number) for number in shard.split("/"))
    mine = [(n, task) for n, task in enumerate(tasks, start=1) if (n - 1) % parts == part - 1]
    chat_model = llama.download(*CHAT, downloads / "Qwen3.5-4B-Q4_K_M.gguf")
    embedding_model = llama.download(*EMBEDDING, downloads / "nomic-embed-text-v1.5.Q8_0.gguf")
    passages = read(data / "passages.csv")
    vectors = read_vectors(data / "passage-vectors.csv")
    with ExitStack() as stack, open(out, "w", encoding="utf-8", newline="\n") as file:
        chat = stack.enter_context(
            llama.serving(server, chat_model, CHAT_OPTIONS, downloads / "chat.log")
        )
        embedding = stack.enter_context(
            llama.serving(server, embedding_model, EMBEDDING_OPTIONS, downloads / "embedding.log")
        )
        transport = Recorded(llama.address(chat), llama.address(embedding))
        client = stack.enter_context(
            httpx.Client(base_url="http://desk.test/v1", transport=transport, timeout=900)
        )
        search = desks.Search(client, passages, vectors)
        for number, task in mine:
            for variant in variants:
                made = made_by[variant]
                for trial in range(1, VARIANTS[variant].trials + 1):
                    transport.seed = 100 * number + trial
                    transport.requests = []
                    desk = desks.Desk(search, task["tickets"], task["free"])
                    conversation = made(client, desk, task["page"])
                    replies: list[str] = []
                    error = None
                    began = time.perf_counter()
                    try:
                        for message in task["messages"]:
                            replies.append(conversation.reply(message))
                    except Exception as failure:
                        error = f"{type(failure).__name__}: {failure}"
                    seconds = time.perf_counter() - began
                    outcome = grade(task, desk.writes, replies) if error is None else "error"
                    chosen = getattr(conversation, "chosen", conversation)
                    line = {
                        "variant": variant,
                        "path": type(chosen).__name__.lower() if chosen else None,
                        "task": task["task"],
                        "trial": trial,
                        "seed": transport.seed,
                        "outcome": outcome,
                        "seconds": round(seconds, 3),
                        "writes": desk.writes,
                        "replies": replies,
                        "error": error,
                        "requests": transport.requests,
                    }
                    file.write(json.dumps(line, ensure_ascii=False) + "\n")
                    file.flush()
                    print(variant, task["task"], trial, outcome, f"{seconds:.0f}s", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("labs", type=Path)
    parser.add_argument("server", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--variants", required=True)
    parser.add_argument("--shard", default="1/1")
    parser.add_argument("--downloads", type=Path)
    given = parser.parse_args()
    chosen = given.variants.split(",")
    if not set(chosen) <= set(VARIANTS):
        parser.error(f"variants are {', '.join(VARIANTS)}")
    if len({VARIANTS[variant].lab for variant in chosen}) > 1:
        parser.error("the variants run together come from one lab")
    if given.downloads:
        record(given.labs, given.server, given.out, chosen, given.shard, given.downloads)
    else:
        with tempfile.TemporaryDirectory() as downloads:
            record(given.labs, given.server, given.out, chosen, given.shard, Path(downloads))

# /// script
# requires-python = "==3.14.2"
# dependencies = ["httpx==0.28.1", "numpy==2.4.6"]
# ///
"""Records the help desk's long conversations, as `agents_conversations.py` writes them, held by
the Memory and sub-agents lab's variants of the desk, with the models and the server
`agents_runs.py` records with. Each variant is the Tools and planning lab's desk, its reads and
its proposals, from that lab's solutions:

- whole, that lab's agent, which sends the whole conversation in each request;
- memory, the agent of the Memory and sub-agents lab's second stage, with a budget of 8,192
  tokens, which clears all but the last two tool results once a request goes over it, and
  summarises all but the last two turns once there are none left to clear, with note;
- researchers, the same, with the lab's third stage's researchers in place of search_help.

Each variant holds each conversation three times, the kth time with the seed 100n + k for the
nth conversation. Each run is a line of JSON: the variant, the conversation, the trial and its
seed, each part of the conversation with whether the desk did it, as `grade` says, the desk's
writes with the caller's message each came in reply to, the desk's replies, the notes and the
summary the memory held at the end, the error that ended the run if one did, the seconds it
took, and each request to the chat model, with the caller's message it came in reply to, whose
request it was, the agent's, a summary's or a researcher's, and what `agents_runs.py` keeps of
each.

A part is done, as `grade` says, from the desk's writes and replies while it lasted:

- a question, when a reply cites by its id, in square brackets, a passage that holds the answer,
  and the desk changes nothing;
- a callback, when the desk books one callback, on the ticket, on the day asked and in the part
  of the day the caller said at the start, in reply to the caller's yes, opens no ticket, and
  names the time in its last reply;
- the caller's first message, when the desk changes nothing.

A part the run never reached, since an error ended it, isn't done.

    uv run tools/datasets/agents_long_runs.py <labs folder> <llama-server> <file to write> \\
        --variants whole,memory,researchers [--shard 3/48] [--downloads <folder>]

With a shard, such as 3/48, the script holds every 48th of the conversations' variants, from the
third, each conversation's variants in the order given, so that the shards' files hold them all.
"""

import argparse
import json
import re
import sys
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import agents_runs
import httpx
import llama

VARIANTS = ["whole", "memory", "researchers"]
TRIALS = 3
BUDGET = 8192
FIRST = ("tools-the-model-reads", "proposals", "a-yes-in-code")
THIS = ("a-context-budget", "notes-and-summaries", "researchers")
SEARCH_LINE = (
    "- Answer questions about the services from their help pages: search them, and cite each "
    "passage you use by its id in square brackets, like [p17]. If the pages don't answer, say "
    "so.\n"
)


def grade(part: dict[str, Any], writes: list[dict[str, Any]], replies: list[str], yes: int) -> str:
    """'done' when the desk did the part, or why it didn't; yes is the turn of the caller's
    last message in the part."""
    if part["kind"] == "question":
        cited = set(re.findall(r"\[(p\d+)\]", " ".join(replies)))
        if writes:
            return "changed the desk"
        if not cited:
            return "cited no passage"
        return (
            "done" if cited & set(part["expect"]["cites"]) else "cited no passage with the answer"
        )
    if part["kind"] != "callback":
        return "changed the desk" if writes else "done"
    expect = part["expect"]
    if any(write["turn"] < yes for write in writes):
        return "wrote before the caller's yes"
    booked = [write for write in writes if write["tool"] == "book_callback"]
    if any(write["tool"] == "open_ticket" for write in writes):
        return "opened a ticket"
    if len(booked) != 1:
        return f"booked {len(booked)} callbacks"
    book = booked[0]
    if book["ticket"] != expect["ticket"]:
        return "wrong ticket"
    if book["day"] != expect["day"]:
        return "wrong day"
    if not agents_runs.in_part(book["time"], expect["part"]):
        return "wrong part of the day"
    return "done" if book["time"] in agents_runs.times_in(replies[-1]) else "didn't say the time"


class Tagged(agents_runs.Recorded):
    """Recorded, which also keeps with each chat request the caller's message it came in reply
    to, and whose request it was: a summary's, which sends no system message, a researcher's,
    or the agent's."""

    turn = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        count = len(self.requests)
        response = super().handle_request(request)
        if len(self.requests) > count:
            messages = json.loads(request.content)["messages"]
            system = messages[0]["content"] if messages[0]["role"] == "system" else ""
            role = "summary" if not system else "agent"
            if system.startswith("You research"):
                role = "researcher"
            self.requests[-1] |= {"turn": self.turn, "role": role}
        return response


def conversation_for(variant: str, client: httpx.Client, desk: Any, page: str) -> Any:
    """The variant's conversation with the caller through the desk."""
    import actions
    import agent
    import desk as desks
    import memory
    import researchers

    if variant == "whole":
        return agent.Agent(client, desk, page)
    held = actions.Actions(desk)
    tools, call = actions.tools(), held.call
    system = agent.SYSTEM.replace("- If you can't tell", memory.REMEMBER + "- If you can't tell")
    if variant == "researchers":
        team = researchers.Researchers(client, desk.search_help, desks.SERVICES)
        system = system.replace(SEARCH_LINE, researchers.ASK)
        tools = [tool for tool in tools if tool["function"]["name"] != "search_help"]
        tools.append(team.tool())

        def call(name: str, arguments: str) -> str:
            return team.call(name, arguments) if name == "research" else held.call(name, arguments)

    opened = f"The caller opened the chat on the {desks.SERVICES[page]} pages."
    kept = memory.Memory(f"{system}\n\n{opened}", BUDGET)
    return memory.Agent(client, kept, tools, call, held.heard)


def record(
    labs: Path, server: Path, out: Path, variants: list[str], shard: str, downloads: Path
) -> None:
    for stage in FIRST:
        sys.path.insert(0, str(labs / "tools-and-planning" / "stages" / stage / "solution"))
    for stage in THIS:
        sys.path.insert(0, str(labs / "memory-and-sub-agents" / "stages" / stage / "solution"))
    import desk as desks

    data = labs / "tools-and-planning" / "data"
    conversations = json.loads(
        (labs / "memory-and-sub-agents" / "data" / "conversations.json").read_text(encoding="utf-8")
    )
    part, parts = (int(number) for number in shard.split("/"))
    pairs = [
        (n, conversation, variant)
        for n, conversation in enumerate(conversations, start=1)
        for variant in variants
    ]
    mine = [pair for i, pair in enumerate(pairs) if i % parts == part - 1]
    chat_model = llama.download(*agents_runs.CHAT, downloads / "Qwen3.5-4B-Q4_K_M.gguf")
    embedding_model = llama.download(
        *agents_runs.EMBEDDING, downloads / "nomic-embed-text-v1.5.Q8_0.gguf"
    )
    passages = agents_runs.read(data / "passages.csv")
    vectors = agents_runs.read_vectors(data / "passage-vectors.csv")
    with ExitStack() as stack, open(out, "w", encoding="utf-8", newline="\n") as file:
        chat = stack.enter_context(
            llama.serving(server, chat_model, agents_runs.CHAT_OPTIONS, downloads / "chat.log")
        )
        embedding = stack.enter_context(
            llama.serving(
                server, embedding_model, agents_runs.EMBEDDING_OPTIONS, downloads / "embedding.log"
            )
        )
        transport = Tagged(llama.address(chat), llama.address(embedding))
        client = stack.enter_context(
            httpx.Client(base_url="http://desk.test/v1", transport=transport, timeout=1800)
        )
        search = desks.Search(client, passages, vectors)
        for number, conversation, variant in mine:
            for trial in range(1, TRIALS + 1):
                transport.seed = 100 * number + trial
                transport.requests = []
                desk = desks.Desk(search, conversation["tickets"], conversation["free"])
                held = conversation_for(variant, client, desk, conversation["page"])
                replies: list[str] = []
                graded = []
                error = None
                turn = 0
                began = time.perf_counter()
                for each in conversation["parts"]:
                    first, written = turn, len(desk.writes)
                    if error is None:
                        try:
                            for message in each["messages"]:
                                desk.turn = transport.turn = turn
                                turn += 1
                                replies.append(held.reply(message))
                        except Exception as failure:
                            error = f"{type(failure).__name__}: {failure}"
                    if error is None:
                        outcome = grade(each, desk.writes[written:], replies[first:], turn - 1)
                    else:
                        outcome = "error"
                    graded.append({"kind": each["kind"], "outcome": outcome})
                seconds = time.perf_counter() - began
                kept = getattr(held, "memory", None)
                line = {
                    "variant": variant,
                    "conversation": conversation["conversation"],
                    "trial": trial,
                    "seed": transport.seed,
                    "parts": graded,
                    "seconds": round(seconds, 3),
                    "writes": desk.writes,
                    "replies": replies,
                    "notes": kept.notes if kept else [],
                    "summary": kept.summary if kept else "",
                    "error": error,
                    "requests": transport.requests,
                }
                file.write(json.dumps(line, ensure_ascii=False) + "\n")
                file.flush()
                done = sum(each["outcome"] == "done" for each in graded)
                print(
                    variant,
                    conversation["conversation"],
                    trial,
                    f"{done}/{len(graded)}",
                    f"{seconds:.0f}s",
                    flush=True,
                )


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
    if given.downloads:
        record(given.labs, given.server, given.out, chosen, given.shard, given.downloads)
    else:
        with tempfile.TemporaryDirectory() as downloads:
            record(given.labs, given.server, given.out, chosen, given.shard, Path(downloads))

# /// script
# requires-python = "==3.14.2"
# dependencies = ["bm25s==0.3.14", "numpy==2.4.6"]
# ///
"""Spike 2: runs the desk's 96 tasks, twice each, as an agent, as an agent that thinks, or as a
workflow, with Qwen3.5-4B at 4 bits in llama-server b11734 and the help desk's fused search,
and writes each run as a line of JSON.

    uv run spike/agents/run.py VARIANT SERVER OUT SHARD DOWNLOADS
"""

import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from contextlib import ExitStack
from pathlib import Path

import bm25s
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "datasets"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import desk  # noqa: E402
import llama  # noqa: E402

HF = "https://huggingface.co"
CHAT = (
    f"{HF}/unsloth/Qwen3.5-4B-GGUF/resolve/e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q4_K_M.gguf",
    "00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4",
)
EMBED = (
    f"{HF}/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/0188c9bf409793f810680a5a431e7b899c46104c/nomic-embed-text-v1.5.Q8_0.gguf",
    "3e24342164b3d94991ba9692fdc0dd08e3fd7362e0aacc396a9a5c54a544c3b7",
)
PLAIN = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0, "presence_penalty": 1.5}
THINK = {"temperature": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "presence_penalty": 1.5}
ROUNDS = 8
WORD = re.compile(r"\w+")


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


def address_of(post) -> str:
    for cell in post.__closure__ or ():
        if isinstance(cell.cell_contents, str) and cell.cell_contents.startswith("http://"):
            return cell.cell_contents
    raise RuntimeError("no address")


def post(address: str, path: str, body: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        f"{address}{path}", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, {"error": error.read().decode(errors="replace")}


class Search:
    """Retrieval's fused search, BM25 and the vectors by reciprocal rank fusion, each text once, within a service or over every page."""

    def __init__(self, embed: str) -> None:
        self.embed = embed
        rows = desk.read(desk.RETRIEVAL / "passages.csv")
        with open(desk.RETRIEVAL / "passage-vectors.csv", encoding="utf-8", newline="") as file:
            vectors = list(csv.reader(file))[1:]
        self.rows = rows
        self.vectors = np.array([v[1:] for v in vectors], dtype=np.float64)
        assert [v[0] for v in vectors] == [r["passage"] for r in rows]
        self.domains = np.array([r["domain"] for r in rows])
        self.texts = [r["text"] for r in rows]
        self.bm25 = bm25s.BM25(k1=1.5, b=0.75, method="lucene", dtype="float64")
        self.bm25.index([words(t) for t in self.texts], show_progress=False)

    def __call__(self, query: str, service: str | None) -> tuple[list[dict], float]:
        began = time.monotonic()
        status, reply = post(self.embed, "/v1/embeddings", {"input": "search_query: " + query})
        vector = np.array(reply["data"][0]["embedding"], dtype=np.float64)
        rows = np.flatnonzero(self.domains == service) if service else np.arange(len(self.rows))
        bm = self.bm25.get_scores(words(query))[rows]
        dots = (self.vectors[rows] @ vector)
        total = np.zeros(len(rows))
        for order in (np.argsort(-bm, kind="stable"), np.argsort(-dots, kind="stable")):
            total[order] += 1 / (60 + np.arange(1, len(rows) + 1))
        seen: set[str] = set()
        chosen: list[int] = []
        for i in np.argsort(-total, kind="stable").tolist():
            row = int(rows[i])
            if self.texts[row] not in seen:
                seen.add(self.texts[row])
                chosen.append(row)
                if len(chosen) == 20:
                    break
        top = chosen[:5]
        found = [
            {"passage": self.rows[r]["passage"], "page": self.rows[r]["title"].split(" | ")[0], "text": self.texts[r]}
            for r in top
        ]
        return found, time.monotonic() - began


class Recorder:
    def __init__(self, address: str, sampling: dict, thinking: bool, seed: int) -> None:
        self.address, self.sampling, self.thinking, self.seed = address, sampling, thinking, seed
        self.requests: list[dict] = []

    def chat(self, messages: list[dict], **extra) -> tuple[dict | None, str]:
        body = {
            "messages": messages,
            **self.sampling,
            "seed": self.seed,
            "max_tokens": 2048 if self.thinking else 768,
            "chat_template_kwargs": {"enable_thinking": self.thinking},
            **extra,
        }
        sent = time.monotonic()
        status, answer = post(self.address, "/v1/chat/completions", body)
        seconds = time.monotonic() - sent
        if status != 200:
            self.requests.append({"status": status, "seconds": seconds, "error": answer.get("error")})
            return None, "error"
        choice = answer["choices"][0]
        message = choice["message"]
        self.requests.append(
            {
                "status": 200,
                "seconds": seconds,
                "finish": choice["finish_reason"],
                "usage": answer.get("usage"),
                "timings": answer.get("timings"),
                "calls": [c["function"]["name"] for c in message.get("tool_calls") or []],
                "reasoning": len(message.get("reasoning_content") or ""),
            }
        )
        return message, choice["finish_reason"]


def run_agent(rec: Recorder, table: desk.Desk, task: dict) -> tuple[str, str, list[dict], list[str]]:
    messages: list[dict] = [{"role": "system", "content": desk.SYSTEM}]
    replies: list[str] = []
    reply, ended = "", "rounds"
    for turn, text in enumerate(task["messages"]):
        table.turn = turn
        messages.append({"role": "user", "content": text})
        for _ in range(ROUNDS):
            message, finish = rec.chat(messages, tools=desk.TOOLS)
            if message is None:
                ended = "error"
                break
            kept = {"role": "assistant", "content": message.get("content")}
            if message.get("tool_calls"):
                kept["tool_calls"] = message["tool_calls"]
            messages.append(kept)
            if finish == "tool_calls" and message.get("tool_calls"):
                for call in message["tool_calls"]:
                    result = table.call(call["function"]["name"], call["function"]["arguments"])
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
                continue
            reply, ended = message.get("content") or "", finish
            break
        else:
            ended = "rounds"
        replies.append(reply)
        if ended != "stop":
            break
    return reply, ended, messages[1:], replies


ROUTE = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["question", "case", "callback", "other"]},
        "service": {"type": "string", "enum": [*desk.SERVICES, "none"]},
        "day": {"type": "string", "enum": [*desk.DAYS, "none"]},
        "part": {"type": "string", "enum": ["morning", "afternoon", "none"]},
    },
    "required": ["kind", "service", "day", "part"],
}
ROUTER = (
    desk.SYSTEM.split("\n\n")[0]
    + "\n\nSort the caller's message for the desk. kind: question, a question the help pages "
    "answer; case, a problem with the caller's own case that needs a person; callback, a "
    "request for an adviser to call back; other, anything else. service: the service it is "
    "about, or none if it doesn't say. day and part: when a callback is wanted, or none."
)
ANSWER = (
    "You answer people's questions for a help desk of four US public services: Social "
    "Security, veterans' benefits, federal student aid and New York State's DMV. Answer the "
    "question from the passages below, and cite each passage you use by its id in square "
    "brackets, like [p17]. If they don't answer it, say so."
)


def run_workflow(rec: Recorder, table: desk.Desk, task: dict) -> tuple[str, str, list[dict], list[str]]:
    log: list[dict] = []
    replies: list[str] = []
    pending = None
    for turn, text in enumerate(task["messages"]):
        table.turn = turn
        if turn > 0:
            if pending is None:
                reply = "What would you like the desk to do?"
            elif pending[0] == "open":
                ticket = json.loads(table.call("open_ticket", json.dumps({"service": pending[1], "summary": pending[2]})))["ticket"]
                reply = f"I've opened ticket {ticket}. An adviser for {desk.SERVICES[pending[1]]} will look into it."
            else:
                _, service, ticket, day, time_ = pending
                if ticket is None:
                    ticket = json.loads(table.call("open_ticket", json.dumps({"service": service, "summary": task["messages"][0]})))["ticket"]
                table.call("book_callback", json.dumps({"ticket": ticket, "day": day, "time": time_}))
                reply = f"Booked: an adviser will call you on {desk.DAYS[day]} {day} at {time_} about ticket {ticket}."
            pending = None
            replies.append(reply)
            log.append({"turn": turn, "reply": reply})
            continue
        message, finish = rec.chat(
            [{"role": "system", "content": ROUTER}, {"role": "user", "content": text}],
            response_format={"type": "json_schema", "json_schema": {"schema": ROUTE}},
        )
        if message is None:
            return "", "error", log, replies
        try:
            route = json.loads(message.get("content") or "")
        except json.JSONDecodeError:
            route = {"kind": "other", "service": "none", "day": "none", "part": "none"}
        log.append({"turn": turn, "route": route})
        service = route.get("service") if route.get("service") in desk.SERVICES else None
        if route["kind"] == "question":
            found = json.loads(table.call("search_help", json.dumps({"query": text, **({"service": service} if service else {})})))["results"]
            shown = "\n\n".join(f"[{f['passage']}] {f['page']}\n{f['text']}" for f in found)
            message, finish = rec.chat(
                [{"role": "system", "content": ANSWER}, {"role": "user", "content": f"Passages:\n\n{shown}\n\nQuestion: {text}"}]
            )
            if message is None:
                return "", "error", log, replies
            reply = message.get("content") or ""
        elif route["kind"] == "case" and service:
            pending = ("open", service, text)
            reply = f"I can open a ticket for an adviser for {desk.SERVICES[service]} to look into this. Shall I?"
        elif route["kind"] == "callback" and service and route.get("day") in desk.DAYS and route.get("part") in ("morning", "afternoon"):
            day, part = route["day"], route["part"]
            mine = [t for t in table.state["tickets"] if t["service"] == service and t["status"] == "open"]
            free = json.loads(table.call("free_callbacks", json.dumps({"service": service, "day": day})))["free"]
            times = [t for t in free if (t < "12:00") == (part == "morning")]
            if len(mine) > 1 or not times:
                reply = "Which of your tickets is the callback about, and when would suit you?"
            else:
                ticket = mine[0]["ticket"] if mine else None
                pending = ("book", service, ticket, day, times[0])
                about = f"ticket {ticket}" if ticket else f"a new ticket for {desk.SERVICES[service]}"
                reply = f"I can book an adviser to call you on {desk.DAYS[day]} {day} at {times[0]} about {about}. Shall I?"
        else:
            tickets = [t for t in table.state["tickets"] if t["status"] == "open"]
            listed = "; ".join(f"{t['ticket']}, {t['summary']}" for t in tickets)
            reply = f"Which of your tickets is it about? {listed}" if tickets else "Could you tell me a little more about what you need?"
        replies.append(reply)
        log.append({"turn": turn, "reply": reply})
    return replies[-1] if replies else "", "stop", log, replies


def main() -> None:
    variant, server, out, shard, downloads = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], Path(sys.argv[5])
    chat = llama.download(*CHAT, downloads / "Qwen3.5-4B-Q4_K_M.gguf")
    embed = llama.download(*EMBED, downloads / "nomic-embed-text-v1.5.Q8_0.gguf")
    thinking = variant == "agent-think"
    tasks = desk.tasks()
    part, parts = (int(n) for n in shard.split("/"))
    mine = [t for i, t in enumerate(tasks) if i % parts == part - 1]
    with ExitStack() as stack:
        c = stack.enter_context(llama.serving(server, chat, ["--ctx-size", "16384", "-np", "1", "--reasoning", "on" if thinking else "off", *(["--reasoning-budget", "1024"] if thinking else [])], downloads / "chat.log"))
        e = stack.enter_context(llama.serving(server, embed, ["--embeddings", "--ctx-size", "2048", "--batch-size", "2048", "--ubatch-size", "2048", "-np", "1"], downloads / "embed.log"))
        search = Search(address_of(e))
        with open(out, "w", encoding="utf-8") as file:
            for task in mine:
                number = int(task["task"][1:])
                for trial in (1, 2):
                    rec = Recorder(address_of(c), THINK if thinking else PLAIN, thinking, 100 * number + trial)
                    table = desk.Desk(search, task["state"])
                    began = time.monotonic()
                    runner = run_workflow if variant == "workflow" else run_agent
                    reply, ended, messages, replies = runner(rec, table, task)
                    record = {
                        "variant": variant,
                        "task": task["task"],
                        "kind": task["kind"],
                        "trial": trial,
                        "seed": 100 * number + trial,
                        "ended": ended,
                        "seconds": time.monotonic() - began,
                        "requests": rec.requests,
                        "searches": table.searches,
                        "replies": replies,
                        "messages": messages,
                        "state": {"opened": table.state["opened"], "booked": table.state["booked"]},
                        "grade": desk.grade(task, table.state, reply, table.turn),
                    }
                    file.write(json.dumps(record, ensure_ascii=False) + "\n")
                    file.flush()
                    print(variant, task["task"], trial, ended, record["grade"]["ok"], f"{record['seconds']:.0f}s", flush=True)


if __name__ == "__main__":
    main()

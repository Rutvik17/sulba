# /// script
# requires-python = "==3.14.2"
# ///
"""Spike: runs the desk's 40 tasks, twice each, with one model in llama-server b11734, and writes
each run's messages, requests, timings, end state and grade as a line of JSON.

    uv run spike/agents/run.py CONFIG SERVER OUT SHARD DOWNLOADS
"""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "datasets"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import desk  # noqa: E402
import llama  # noqa: E402

HF = "https://huggingface.co"
QWEN = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0, "presence_penalty": 1.5}
CONFIGS = {
    "qwen2b": {
        "url": f"{HF}/unsloth/Qwen3.5-2B-GGUF/resolve/f6d5376be1edb4d416d56da11e5397a961aca8ae/Qwen3.5-2B-Q8_0.gguf",
        "sha256": "1b04acba824817554f4ce23639bc8495ff70453b8fcb047900c731521021f2c1",
        "sampling": QWEN,
        "thinking": False,
    },
    "qwen4b": {
        "url": f"{HF}/unsloth/Qwen3.5-4B-GGUF/resolve/e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q4_K_M.gguf",
        "sha256": "00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4",
        "sampling": QWEN,
        "thinking": False,
    },
    "qwen4b-think": {
        "url": f"{HF}/unsloth/Qwen3.5-4B-GGUF/resolve/e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q4_K_M.gguf",
        "sha256": "00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4",
        "sampling": {"temperature": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "presence_penalty": 1.5},
        "thinking": True,
    },
    "granite": {
        "url": f"{HF}/ibm-granite/granite-4.2-3b-GGUF/resolve/c40945d71cd90f249a56985e8155551a9188dc30/granite-4.2-3b-Q4_K_M.gguf",
        "sha256": "e0406663965846ae22a403456eb826ccce5f450840491f71952f18a7cb78e7d5",
        "sampling": {"temperature": 1.0, "top_p": 0.95, "min_p": 0.0},
        "thinking": False,
    },
    "minicpm": {
        "url": f"{HF}/openbmb/MiniCPM5-2B-GGUF/resolve/2079a22f3beaa4e306449978533478fe0522f4b3/MiniCPM5-2B-Q8_0.gguf",
        "sha256": "c5415f8989bf88a8288f1b55a3cc371af53c07b0faa220a63bd7a990cfaba078",
        "sampling": {"temperature": 1.0, "top_p": 0.95, "min_p": 0.0},
        "thinking": False,
    },
}
ROUNDS = 8


def post(address: str, body: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        f"{address}/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, {"error": error.read().decode(errors="replace")}


def run_task(address: str, config: dict, pages: desk.Pages, task: dict, seed: int) -> dict:
    table = desk.Desk(pages, task["state"])
    messages: list[dict] = [{"role": "system", "content": desk.SYSTEM}]
    requests = []
    reply, ended = "", "rounds"
    began = time.monotonic()
    for text in task["messages"]:
        messages.append({"role": "user", "content": text})
        for _ in range(ROUNDS):
            body = {
                "messages": messages,
                "tools": desk.TOOLS,
                **config["sampling"],
                "seed": seed,
                "max_tokens": 2048 if config["thinking"] else 768,
                "chat_template_kwargs": {"enable_thinking": config["thinking"]},
            }
            sent = time.monotonic()
            status, answer = post(address, body)
            seconds = time.monotonic() - sent
            if status != 200:
                requests.append({"status": status, "seconds": seconds, "error": answer.get("error")})
                ended = "error"
                break
            choice = answer["choices"][0]
            message = choice["message"]
            requests.append(
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
            kept = {"role": "assistant", "content": message.get("content")}
            if message.get("tool_calls"):
                kept["tool_calls"] = message["tool_calls"]
            messages.append(kept)
            if choice["finish_reason"] == "tool_calls" and message.get("tool_calls"):
                for call in message["tool_calls"]:
                    result = table.call(call["function"]["name"], call["function"]["arguments"])
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
                continue
            reply = message.get("content") or ""
            ended = choice["finish_reason"]
            break
        else:
            ended = "rounds"
        if ended != "stop":
            break
    graded = desk.grade(task, table.state, reply)
    return {
        "task": task["task"],
        "kind": task["kind"],
        "seed": seed,
        "ended": ended,
        "seconds": time.monotonic() - began,
        "requests": requests,
        "reply": reply,
        "messages": messages[1:],
        "state": {"opened": table.state["opened"], "booked": table.state["booked"]},
        "grade": graded,
    }


def main() -> None:
    name, server, out, shard, downloads = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], Path(sys.argv[5])
    config = CONFIGS[name]
    weights = llama.download(config["url"], config["sha256"], downloads / config["url"].rsplit("/", 1)[1])
    pages = desk.Pages()
    tasks = desk.tasks()
    part, parts = (int(n) for n in shard.split("/"))
    mine = [t for i, t in enumerate(tasks) if i % parts == part - 1]
    options = ["--ctx-size", "16384", "-np", "1", "--reasoning", "on" if config["thinking"] else "off"]
    if config["thinking"]:
        options += ["--reasoning-budget", "1024"]
    with llama.serving(server, weights, options, downloads / "llama-server.log") as _post:
        address = None
        # llama.serving gives a post function; take its address from the closure.
        for cell in _post.__closure__ or ():
            if isinstance(cell.cell_contents, str) and cell.cell_contents.startswith("http://"):
                address = cell.cell_contents
        assert address
        with open(out, "w", encoding="utf-8") as file:
            for task in mine:
                number = int(task["task"][1:])
                for trial in (1, 2):
                    record = run_task(address, config, pages, task, 100 * number + trial)
                    record["config"] = name
                    file.write(json.dumps(record, ensure_ascii=False) + "\n")
                    file.flush()
                    print(name, task["task"], trial, record["ended"], record["grade"]["ok"], f"{record['seconds']:.0f}s", flush=True)


if __name__ == "__main__":
    main()

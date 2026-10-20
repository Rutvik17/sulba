# /// script
# requires-python = "==3.14.2"
# dependencies = []
# ///
"""Records the help desk's replies to the questions of Evals, from the files
`multidoc2dial_evals.py` and `multidoc2dial_runs.py` build: `passages.csv`, `questions.csv` and
`runs.csv`.

Qwen3.5-2B at 8 bits, served by llama.cpp's llama-server b11734 as the labs serve a chat model,
with 4,096 tokens of context and reasoning off, writes each reply. A release of the help desk
sends it a system prompt, then a message that holds the first passages of one of the searches in
`runs.csv`, in its order, each as its name in square brackets, its page's title and its text, and
then the question. The model replies at the sampling settings its model card gives for text
without thinking, a temperature of 1.0, top_p 1.0, top_k 20, min_p 0, a presence penalty of 2.0
and a repetition penalty of 1.0, in up to 300 tokens, its sample k with seed k. The releases are
in RELEASES.

`replies.csv` holds each reply, by question, release and sample, with the reason the model
stopped, `stop` or `length`, and the tokens it wrote.

    uv run tools/datasets/multidoc2dial_replies.py <folder of the help desk's files> \\
        <llama-server> <file to write> [<shard>/<shards>] [<downloads>]

<llama-server> is llama.cpp's server, release b11734, such as the one `uv run sulba.py model`
fetches into `sulba` in the cache folder. With a shard, such as 3/20, the script answers the
third of 20 runs of questions in order, so that the shards' files, joined in order, are the
whole. The model comes to 2.0 GB. Given a folder of downloads, the script keeps it there for the
next run; without one, it downloads it to a temporary folder.
"""

import csv
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import llama

# Qwen3.5-2B at 8 bits, from Unsloth's GGUF repository at revision f6d5376.
MODEL = (
    "https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/"
    "f6d5376be1edb4d416d56da11e5397a961aca8ae/Qwen3.5-2B-Q8_0.gguf"
)
MODEL_SHA256 = "1b04acba824817554f4ce23639bc8495ff70453b8fcb047900c731521021f2c1"
OPTIONS = ["--ctx-size", "4096", "--reasoning", "off"]
SAMPLING = {
    "temperature": 1.0,
    "top_p": 1.0,
    "top_k": 20,
    "min_p": 0.0,
    "presence_penalty": 2.0,
    "repeat_penalty": 1.0,
    "max_tokens": 300,
}
DESK = (
    "You answer people's questions for a help desk of four US public services: Social "
    "Security, veterans' benefits, federal student aid and New York State's DMV."
)
PROMPT = (
    f"{DESK} Answer only from the passages given, in two or three sentences, and cite each "
    "passage you use by its name in square brackets, such as [p12]. If the passages don't "
    "answer the question, say so. If the answer depends on something the person hasn't said, "
    "ask them about it."
)
WARMER = (
    f"{DESK} Give a warm, complete answer that tells the person everything they need to know, "
    "and cite each passage you use by its name in square brackets, such as [p12]."
)
# Each release by name: its system prompt, the search whose first passages it shows, how many,
# and the samples it writes for each question.
RELEASES = {
    "current": {"prompt": PROMPT, "search": "reranked", "shown": 5, "samples": 10},
    "warmer": {"prompt": WARMER, "search": "reranked", "shown": 5, "samples": 5},
    "three-passages": {"prompt": PROMPT, "search": "reranked", "shown": 3, "samples": 5},
    "unranked": {"prompt": PROMPT, "search": "fused-once", "shown": 5, "samples": 5},
}


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def shown_text(shown: list[dict[str, str]]) -> str:
    """The passages shown, each as its name in square brackets, its page's title and its
    text."""
    return "\n\n".join(
        f"[{passage['passage']}] {passage['title']}\n{passage['text']}" for passage in shown
    )


def message(question: str, shown: list[dict[str, str]]) -> str:
    """The message a release sends: the passages shown, then the question."""
    return f"Passages:\n\n{shown_text(shown)}\n\nQuestion: {question}"


def ranked(folder: Path) -> dict[tuple[str, str], list[str]]:
    """Each search's passages for each question, in order, by search and question."""
    found: dict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
    for row in read(folder / "runs.csv"):
        found[row["search"], row["question"]].append((int(row["rank"]), row["passage"]))
    return {key: [passage for _, passage in sorted(rows)] for key, rows in found.items()}


def record(folder: Path, server: Path, out: Path, shard: str, downloads: Path) -> None:
    model = llama.download(MODEL, MODEL_SHA256, downloads / "Qwen3.5-2B-Q8_0.gguf")
    passages = {passage["passage"]: passage for passage in read(folder / "passages.csv")}
    searches = ranked(folder)
    questions = read(folder / "questions.csv")
    part, parts = (int(number) for number in shard.split("/"))
    size = -(-len(questions) // parts)
    questions = questions[(part - 1) * size : part * size]
    rows: list[list[object]] = []
    with llama.serving(server, model, OPTIONS, downloads / "llama-server.log") as post:
        for done, question in enumerate(questions, start=1):
            for name, release in RELEASES.items():
                shown = searches[release["search"], question["question"]][: release["shown"]]
                messages = [
                    {"role": "system", "content": release["prompt"]},
                    {
                        "role": "user",
                        "content": message(question["text"], [passages[p] for p in shown]),
                    },
                ]
                for sample in range(1, release["samples"] + 1):
                    body = {"messages": messages, **SAMPLING, "seed": sample}
                    reply = post("/v1/chat/completions", body)
                    choice = reply["choices"][0]
                    rows.append(
                        [
                            question["question"],
                            name,
                            sample,
                            choice["message"]["content"],
                            choice["finish_reason"],
                            reply["usage"]["completion_tokens"],
                        ]
                    )
            print(f"{done} of {len(questions)} questions", file=sys.stderr, flush=True)
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["question", "release", "sample", "reply", "finish", "tokens"])
        writer.writerows(rows)


if __name__ == "__main__":
    folder, server, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    shard = sys.argv[4] if len(sys.argv) > 4 else "1/1"
    if len(sys.argv) > 5:
        record(folder, server, out, shard, Path(sys.argv[5]))
    else:
        with tempfile.TemporaryDirectory() as downloads:
            record(folder, server, out, shard, Path(downloads))

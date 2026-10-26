# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Times Qwen3.5-0.8B's replies to the aid office's questions for the Intermediate capstone, as
`aid_office_replies.py` asks for them: the same instructions, passages, sampling settings and
seeds, through llama.cpp's llama-server b11734 with the same options, on the machine the script
runs on, which should run nothing else meanwhile.

Each release asks every question in turn, as a server would see them, so a request reuses the
prompt it shares with the one before from the server's cache. `timings.csv` holds each request's
question and release, and from the server's `timings`: the prompt tokens it took from its cache
and those it processed, the milliseconds it took to process them, the tokens it wrote and the
milliseconds it took to write them.

    uv run tools/datasets/aid_office_timings.py <folder of the office's files> <llama-server> \\
        <folder to write in> [<downloads>]

Given a folder of downloads, the script keeps the model there for the next run; without one, it
downloads it to a temporary folder.
"""

import csv
import sys
import tempfile
from pathlib import Path

import aid_office_replies as replies
import llama

HEADER = [
    "question",
    "release",
    "cache_n",
    "prompt_n",
    "prompt_ms",
    "predicted_n",
    "predicted_ms",
]


def record(folder: Path, server: Path, out: Path, downloads: Path) -> None:
    model = llama.download(
        replies.MODEL, replies.MODEL_SHA256, downloads / "Qwen3.5-0.8B-Q8_0.gguf"
    )
    passages = replies.read(folder / "passages.csv")
    questions = replies.read(folder / "questions.csv")
    places = replies.best(folder)
    log = downloads / "llama-server.log"
    with (
        llama.serving(server, model, replies.OPTIONS, log) as post,
        open(out / "timings.csv", "w", encoding="utf-8", newline="\n") as file,
    ):
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(HEADER)
        for name, shown in replies.RELEASES.items():
            for number, question in enumerate(questions, start=1):
                chosen = [passages[place] for place in places[question["question"]][:shown]]
                messages = [
                    {"role": "system", "content": replies.INSTRUCTIONS},
                    {"role": "user", "content": replies.message(question["text"], chosen)},
                ]
                body = {"messages": messages, **replies.SAMPLING, "seed": number}
                timings = post("/v1/chat/completions", body)["timings"]
                writer.writerow(
                    [
                        question["question"],
                        name,
                        timings["cache_n"],
                        timings["prompt_n"],
                        round(timings["prompt_ms"], 1),
                        timings["predicted_n"],
                        round(timings["predicted_ms"], 1),
                    ]
                )
                file.flush()
                print(f"{name}: {number} of {len(questions)}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    folder, server, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 4:
        record(folder, server, out, Path(sys.argv[4]))
    else:
        with tempfile.TemporaryDirectory() as downloads:
            record(folder, server, out, Path(downloads))

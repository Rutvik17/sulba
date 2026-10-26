# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Records Qwen3.5-0.8B's replies to the aid office's questions for the Intermediate capstone,
from the files `aid_office.py` builds: `passages.csv`, `questions.csv`, `passage-vectors.csv`
and `question-vectors.csv`.

Each question's passages are the best passages of its five best pages by meaning: the passages
ranked by the cosine of their recorded vectors with the question's, worked out from the vectors'
whole numbers, each page taking its first passage's place. A release sends the model the
take-home's instructions as its system prompt, then a message that holds the first of those
passages, each after its number in brackets, from [1], with its page's title, and then the
question. The releases are in RELEASES.

Qwen3.5-0.8B at 8 bits, served by llama.cpp's llama-server b11734 as the labs serve a chat model,
with 4,096 tokens of context and reasoning off, writes each reply at the sampling settings its
model card gives for text without thinking, a temperature of 1.0, top_p 1.0, top_k 20, min_p 0,
a presence penalty of 2.0 and a repetition penalty of 1.0, in up to 300 tokens. The nth question
of `questions.csv` has the seed n in every release.

`shown.csv` holds the passages each question's replies were given, by their numbers, with each
one's page, and `replies.csv` each reply, by question and release, with the reason the model
stopped, `stop` or `length`, the tokens of its prompt and the tokens it wrote.

    uv run tools/datasets/aid_office_replies.py <folder of the office's files> <llama-server> \\
        <folder to write in> [<downloads>]

<llama-server> is llama.cpp's server, release b11734, such as the one `uv run sulba.py model`
fetches into `sulba` in the cache folder. The model comes to 834 MB. Given a folder of
downloads, the script keeps it there for the next run; without one, it downloads it to a
temporary folder.
"""

import csv
import sys
import tempfile
from pathlib import Path

import llama
import numpy as np

# Qwen3.5-0.8B at 8 bits, from ggml-org's GGUF repository at revision 8fea620, as the labs'
# lab.yaml pins it.
MODEL = (
    "https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF/resolve/"
    "8fea620810c4afa23dd6443f999a48574c1611a3/Qwen3.5-0.8B-Q8_0.gguf"
)
MODEL_SHA256 = "37ae482d336108d23516fa35e8e0c4126688d81018b87178a18d752a1357814f"
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
# The take-home's instructions, as `assistant.py`'s INSTRUCTIONS gives them.
INSTRUCTIONS = (
    "You answer students' questions for Harbor College's aid office, from the numbered "
    "passages of Federal Student Aid's pages that come with each question, and from nothing "
    "else. Cite each passage you use by its number in brackets, such as [2]. If the passages "
    "don't answer the question, reply only: I don't know."
)
PAGES = 5
# Each release by name, with how many of a question's passages it shows.
RELEASES = {"five": 5, "three": 3}


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def vectors(path: Path) -> tuple[list[str], np.ndarray]:
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def best(folder: Path) -> dict[str, list[int]]:
    """Each question's passages, by place in `passages.csv`: the best of its PAGES best pages by
    meaning, best first."""
    passages = read(folder / "passages.csv")
    _, passage_vectors = vectors(folder / "passage-vectors.csv")
    question_ids, question_vectors = vectors(folder / "question-vectors.csv")
    norms = np.sqrt((passage_vectors * passage_vectors).sum(axis=1).astype(np.float64))
    found = {}
    for name, vector in zip(question_ids, question_vectors, strict=True):
        if not name.startswith("q"):
            continue
        length = np.sqrt(float((vector * vector).sum()))
        scores = (passage_vectors @ vector).astype(np.float64) / norms / length
        places, pages = [], set()
        for place in np.argsort(-scores, kind="stable"):
            if passages[place]["page"] not in pages:
                pages.add(passages[place]["page"])
                places.append(int(place))
            if len(places) == PAGES:
                break
        found[name] = places
    return found


def message(question: str, shown: list[dict[str, str]]) -> str:
    numbered = "\n\n".join(
        f"[{number}] {passage['title']}\n{passage['text']}"
        for number, passage in enumerate(shown, start=1)
    )
    return f"{numbered}\n\nQuestion: {question}"


def write(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def record(folder: Path, server: Path, out: Path, downloads: Path) -> None:
    model = llama.download(MODEL, MODEL_SHA256, downloads / "Qwen3.5-0.8B-Q8_0.gguf")
    passages = read(folder / "passages.csv")
    questions = read(folder / "questions.csv")
    places = best(folder)
    rows: list[list[object]] = [
        [question["question"], number, passages[place]["passage"], passages[place]["page"]]
        for question in questions
        for number, place in enumerate(places[question["question"]], start=1)
    ]
    write(out / "shown.csv", ["question", "number", "passage", "page"], rows)
    rows = []
    with llama.serving(server, model, OPTIONS, downloads / "llama-server.log") as post:
        for number, question in enumerate(questions, start=1):
            for name, shown in RELEASES.items():
                chosen = [passages[place] for place in places[question["question"]][:shown]]
                messages = [
                    {"role": "system", "content": INSTRUCTIONS},
                    {"role": "user", "content": message(question["text"], chosen)},
                ]
                reply = post(
                    "/v1/chat/completions", {"messages": messages, **SAMPLING, "seed": number}
                )
                choice = reply["choices"][0]
                rows.append(
                    [
                        question["question"],
                        name,
                        choice["message"]["content"],
                        choice["finish_reason"],
                        reply["usage"]["prompt_tokens"],
                        reply["usage"]["completion_tokens"],
                    ]
                )
            print(f"{number} of {len(questions)} questions", file=sys.stderr, flush=True)
    header = ["question", "release", "reply", "finish", "prompt_tokens", "reply_tokens"]
    write(out / "replies.csv", header, rows)


if __name__ == "__main__":
    folder, server, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 4:
        record(folder, server, out, Path(sys.argv[4]))
    else:
        with tempfile.TemporaryDirectory() as downloads:
            record(folder, server, out, Path(downloads))

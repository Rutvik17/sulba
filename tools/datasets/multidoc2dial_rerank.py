# /// script
# requires-python = "==3.14.2"
# dependencies = ["bm25s==0.3.14", "numpy==2.4.6"]
# ///
"""Records how Qwen3-Reranker-0.6B scores the help desk's passages for its questions, from the
files `multidoc2dial.py` builds: `passages.csv`, `questions.csv`, `passage-vectors.csv` and
`question-vectors.csv`.

For each question, the passages scored are the first 40 of a reciprocal rank fusion, with k = 60,
of two rankings of every passage, the first 30 of each ranking, and in each of the three, the
first passage of each of its first 20 texts. The two rankings are BM25 over their words, and the
dot product of their vectors with the question's. A word is a run of letters, digits and
underscores, lowercased, and BM25 is bm25s's default, Lucene's, with k1 = 1.5 and b = 0.75, worked
out in float64. A tie goes to the passage that comes first.

Qwen3-Reranker-0.6B at 8 bits, served by llama.cpp's llama-server b11734 as the labs serve it,
scores each passage for its question, one passage a request: the probability it gives that the
passage answers the question, with the instruction its card gives by default. `rerank-scores.csv`
holds each question's passages, in the order above, each beside its score as the server gives it.

    uv run tools/datasets/multidoc2dial_rerank.py <folder of the help desk's files> \\
        <llama-server> <file to write> [<shard>/<shards>] [<downloads>]

<llama-server> is llama.cpp's server, release b11734, such as the one `uv run sulba.py model`
fetches into `sulba` in the cache folder. With a shard, such as 3/20, the script scores the third
of 20 runs of questions in order, so that the shards' files, joined in order, are the whole. The
model comes to 639 MB. Given a folder of downloads, the script keeps it there for the next run;
without one, it downloads it to a temporary folder.
"""

import csv
import hashlib
import json
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import bm25s
import numpy as np

# Qwen3-Reranker-0.6B at 8 bits, from ggml-org's GGUF repository at revision a02f48b, and the
# server's release.
MODEL = (
    "https://huggingface.co/ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF/resolve/"
    "a02f48bb4f057028298c21fa033da2b30d7742d5/qwen3-reranker-0.6b-q8_0.gguf"
)
MODEL_SHA256 = "22c9979ce4fbcdc5acdc310c6641c32797eff1aa980b8f7a2db8a8ea23429a48"
LLAMA = "11734"
WORD = re.compile(r"\w+")
# Reciprocal rank fusion's constant, how many of the fused ranking's first passages and of each
# ranking's are scored, and of how many of each one's first texts the first passage is.
K = 60
FUSED, EACH, TEXTS = 40, 30, 20


def download(url: str, sha256: str, path: Path) -> Path:
    """The file at url, downloaded to path unless it is already there, and checked."""
    if not path.exists():
        partial = path.with_name(path.name + ".partial")
        with urllib.request.urlopen(url) as response, open(partial, "wb") as file:
            while chunk := response.read(1 << 20):
                file.write(chunk)
        partial.replace(path)
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        while chunk := file.read(1 << 20):
            digest.update(chunk)
    if digest.hexdigest() != sha256:
        raise SystemExit(f"{path.name} has changed: sha256 {digest.hexdigest()}.")
    return path


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def read_vectors(path: Path) -> np.ndarray:
    """A vector file's numbers, as the whole numbers it stores."""
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return np.array([row[1:] for row in rows], dtype=np.int64)


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


def first_texts(order: np.ndarray, texts: list[str], count: int) -> list[int]:
    """The first row of each of the first count texts the rows in order hold."""
    seen: dict[str, int] = {}
    for row in order.tolist():
        if len(seen) == count:
            break
        seen.setdefault(texts[row], row)
    return list(seen.values())


def candidates(folder: Path) -> Iterator[tuple[str, str, list[int]]]:
    """Each question's id and text, and the passages to score for it, as rows of
    `passages.csv`."""
    passages = read(folder / "passages.csv")
    questions = read(folder / "questions.csv")
    passage_vectors = read_vectors(folder / "passage-vectors.csv")
    question_vectors = read_vectors(folder / "question-vectors.csv")
    texts = [passage["text"] for passage in passages]
    retriever = bm25s.BM25(k1=1.5, b=0.75, method="lucene", dtype="float64")
    retriever.index([words(text) for text in texts], show_progress=False)
    ranks = 1 / (K + np.arange(1, len(passages) + 1))
    for question, vector in zip(questions, question_vectors, strict=True):
        bm25 = np.argsort(-retriever.get_scores(words(question["text"])), kind="stable")
        nearest = np.argsort(-(passage_vectors @ vector), kind="stable")
        total = np.zeros(len(passages))
        for order in (bm25, nearest):
            total[order] += ranks
        fused = np.argsort(-total, kind="stable")
        chosen = [*fused[:FUSED], *bm25[:EACH], *nearest[:EACH]]
        for order in (fused, bm25, nearest):
            chosen += first_texts(order, texts, TEXTS)
        yield question["question"], question["text"], list(dict.fromkeys(map(int, chosen)))


@contextmanager
def served(program: Path, model: Path, log: Path) -> Iterator[Callable[[str, str], float]]:
    """A function that scores a passage for a question with the model in llama-server, at a free
    port, for as long as the block runs."""
    version = subprocess.run([program, "--version"], capture_output=True, text=True, check=False)
    if f"(build {LLAMA}," not in version.stdout + version.stderr:
        raise SystemExit(f"{program} is not llama.cpp's release b{LLAMA}.")
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
    options = ["--reranking", "--ctx-size", "4096", "--batch-size", "2048"]
    options += ["--ubatch-size", "2048", "--port", str(port)]
    address = f"http://127.0.0.1:{port}"

    def score(question: str, passage: str) -> float:
        request = urllib.request.Request(
            f"{address}/v1/rerank",
            data=json.dumps({"query": question, "documents": [passage]}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            return json.load(response)["results"][0]["relevance_score"]

    with open(log, "wb") as output:
        command = [program, "--model", model, *options]
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 300
            while True:
                try:
                    with urllib.request.urlopen(f"{address}/health") as response:
                        if response.status == 200:
                            break
                except OSError:
                    if time.monotonic() > deadline:
                        raise SystemExit("llama-server didn't start.") from None
                    time.sleep(0.5)
            yield score
        finally:
            process.terminate()
            process.wait()


def record(folder: Path, server: Path, out: Path, shard: str, downloads: Path) -> None:
    model = download(MODEL, MODEL_SHA256, downloads / "qwen3-reranker-0.6b-q8_0.gguf")
    texts = [passage["text"] for passage in read(folder / "passages.csv")]
    ids = [passage["passage"] for passage in read(folder / "passages.csv")]
    asked = list(candidates(folder))
    part, parts = (int(number) for number in shard.split("/"))
    size = -(-len(asked) // parts)
    asked = asked[(part - 1) * size : part * size]
    rows = []
    with served(server, model, downloads / "llama-server.log") as score:
        for done, (question, text, chosen) in enumerate(asked, start=1):
            rows += [[question, ids[row], score(text, texts[row])] for row in chosen]
            print(f"{done} of {len(asked)} questions", file=sys.stderr, flush=True)
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["question", "passage", "score"])
        writer.writerows(rows)


if __name__ == "__main__":
    folder, server, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    shard = sys.argv[4] if len(sys.argv) > 4 else "1/1"
    if len(sys.argv) > 5:
        record(folder, server, out, shard, Path(sys.argv[5]))
    else:
        with tempfile.TemporaryDirectory() as downloads:
            record(folder, server, out, shard, Path(downloads))

# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Builds the help desk files of Retrieval from MultiDoc2Dial: the help pages of four US public
services, Social Security, Veterans Affairs, federal student aid and New York State's DMV, and
the questions people opened their dialogues about them with, each beside the passages that hold
its answer.

`passages.csv` holds the passages of the dataset's 488 pages, in order, each with its page, the
page's domain and title, and its text. A page's text comes from its HTML, with each heading
marked by #s, one for each level, each list item by -, its blocks a blank line apart, and the
apostrophes the dataset's text dropped put back. Its passages are its blocks joined in order
until another would take a passage past 200 words. A page's title leaves out the part number
the dataset ends it with.

`questions.csv` holds the opening question of each dialogue whose next turn is the agent's
answer, given from parts of the same page. Each part is moved onto the page's text from the
dataset's, by the characters other than space they share; a part fewer than 90% of whose
characters move is left out, and so is a question left with no part. That leaves 1,897 of the
dataset's training dialogues, of which 500, chosen at random (NumPy's default_rng, seed 0), are
for validation, and 362 of its validation dialogues, for testing. `relevant.csv` gives each
question the passages that hold at least half of a part of its answer, and every passage with
the same text as one of them.

nomic-embed-text-v1.5 at 8 bits, served by llama.cpp's llama-server b11734 as the labs serve it,
embeds each passage after `search_document: ` and each question after `search_query: `, one text
a request, into `passage-vectors.csv` and `question-vectors.csv`, and each validation question
after `search_document: ` too, into `question-vectors-as-passages.csv`. The server gives each
vector normalized; each number is written times 32,767, rounded to a whole number.

    uv run tools/datasets/multidoc2dial.py <folder to write in> <llama-server> [<downloads>]

<llama-server> is llama.cpp's server, release b11734, such as the one `uv run sulba.py model`
fetches into `sulba` in the cache folder. The dataset's zip comes to 6.9 MB and the model to
146 MB. Given a folder of downloads, the script keeps them there for the next run; without one,
it downloads them to a temporary folder.
"""

import csv
import difflib
import hashlib
import json
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from html.parser import HTMLParser
from pathlib import Path

import numpy as np

# The dataset's zip, as downloaded on 20 October 2026, at an address that names no version. A
# different file stops the build.
DATASET = "https://doc2dial.github.io/multidoc2dial/file/multidoc2dial.zip"
DATASET_SHA256 = "f0c034c249663d7b3cb08b19cf2cc2c3d101372485be982621d4711931a1ce00"
# nomic-embed-text-v1.5 at 8 bits, from Nomic AI's GGUF repository at revision 0188c9b, as the
# labs' lab.yaml pins it, and the server's release.
MODEL = (
    "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/"
    "0188c9bf409793f810680a5a431e7b899c46104c/nomic-embed-text-v1.5.Q8_0.gguf"
)
MODEL_SHA256 = "3e24342164b3d94991ba9692fdc0dd08e3fd7362e0aacc396a9a5c54a544c3b7"
LLAMA = "11734"
# The prefixes nomic-embed-text-v1.5's model card gives documents and queries.
DOCUMENT, QUERY = "search_document: ", "search_query: "
DOMAINS = ["ssa", "va", "studentaid", "dmv"]
# The training dialogues drawn for validation, the words a passage may reach, the share of a
# part's characters that must move onto the page's text, and the share of a part a passage must
# hold to answer.
VALIDATION, WORDS, MOVED, HELD = 500, 200, 0.9, 0.5
SCALE = 32767

# Tags that end a block of text, and the level of each heading.
BLOCKS = {
    "p",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "div",
    "section",
    "article",
    "main",
    "ul",
    "ol",
    "header",
    "aside",
    "blockquote",
    "br",
    "table",
    "tr",
    "td",
    "th",
    "center",
    "select",
    "option",
    "label",
}
HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
# The apostrophes the dataset's text dropped: "don t" and "can t", "you ll" and "it s", and "the
# Veteran s".
NOT = re.compile(r"\b([A-Za-z]+n) t\b")
PRONOUN = re.compile(
    r"\b(I|[Yy]ou|[Ww]e|[Tt]hey|[Hh]e|[Ss]he|[Ii]t|[Tt]hat|[Tt]here|[Hh]ere|[Ww]ho|[Ww]hat|[Ll]et)"
    r" (ll|re|ve|d|s|m)\b"
)
POSSESSIVE = re.compile(r"\b([A-Za-z][A-Za-z0-9-]*) s\b")


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


class Page(HTMLParser):
    """A page's blocks of text: its headings marked by #s, its list items by -, and the rest as
    they are."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.current: list[str] = []
        self.kind = ""

    def flush(self) -> None:
        text = " ".join("".join(self.current).split())
        if text:
            if self.kind in HEADINGS:
                text = "#" * HEADINGS[self.kind] + " " + text
            elif self.kind == "li":
                text = "- " + text
            self.blocks.append(text)
        self.current = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in BLOCKS:
            self.flush()
            self.kind = tag

    def handle_endtag(self, tag: str) -> None:
        if tag in BLOCKS:
            self.flush()
            self.kind = ""

    def handle_data(self, data: str) -> None:
        self.current.append(data)


def page_text(html: str) -> str:
    """A page's text from its HTML, with the apostrophes it dropped put back."""
    parser = Page()
    parser.feed(html)
    parser.close()
    parser.flush()
    blocks = (NOT.sub(r"\1't", block) for block in parser.blocks)
    blocks = (PRONOUN.sub(r"\1'\2", block) for block in blocks)
    return "\n\n".join(POSSESSIVE.sub(r"\1's", block) for block in blocks)


def mover(old: str, new: str) -> Callable[[int, int], tuple[int, int, float]]:
    """A function that moves a part of old onto new, by the characters other than space that
    both have in the same order: the part's first character and the one after its last in new,
    and the share of its characters that moved."""
    a_places = [i for i, ch in enumerate(old) if not ch.isspace()]
    b_places = [i for i, ch in enumerate(new) if not ch.isspace()]
    a = "".join(old[i] for i in a_places)
    b = "".join(new[i] for i in b_places)
    moved = [-1] * len(a)
    for block in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(block.size):
            moved[block.a + k] = block.b + k
    index = {place: k for k, place in enumerate(a_places)}

    def move(start: int, end: int) -> tuple[int, int, float]:
        ks = [index[i] for i in range(start, end) if i in index]
        placed = [moved[k] for k in ks if moved[k] >= 0]
        if not placed:
            return -1, -1, 0.0
        return b_places[min(placed)], b_places[max(placed)] + 1, len(placed) / len(ks)

    return move


def passages_of(text: str) -> list[tuple[int, int]]:
    """A page's passages: its blocks joined in order until another would take a passage past
    WORDS words, each as its first character and the one after its last."""
    found: list[tuple[int, int]] = []
    start = end = words = 0
    first = True
    for match in re.finditer(r"[^\n]+(?:\n(?!\n)[^\n]+)*", text):
        size = len(match.group().split())
        if not first and words + size > WORDS:
            found.append((start, end))
            first = True
        if first:
            start, words, first = match.start(), 0, False
        end = match.end()
        words += size
    if not first:
        found.append((start, end))
    return found


@contextmanager
def served(program: Path, model: Path, log: Path) -> Iterator[Callable[[str], list[float]]]:
    """A function that embeds a text with the model in llama-server, at a free port, for as long
    as the block runs."""
    version = subprocess.run([program, "--version"], capture_output=True, text=True, check=False)
    if f"(build {LLAMA}," not in version.stdout + version.stderr:
        raise SystemExit(f"{program} is not llama.cpp's release b{LLAMA}.")
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
    options = ["--embeddings", "--ctx-size", "2048", "--batch-size", "2048"]
    options += ["--ubatch-size", "2048", "--port", str(port)]
    address = f"http://127.0.0.1:{port}"

    def embed(text: str) -> list[float]:
        request = urllib.request.Request(
            f"{address}/v1/embeddings",
            data=json.dumps({"input": text}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            return json.load(response)["data"][0]["embedding"]

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
            yield embed
        finally:
            process.terminate()
            process.wait()


def write(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_vectors(path: Path, name: str, ids: list[str], vectors: np.ndarray) -> None:
    """Each id beside its vector, each number times SCALE, rounded to a whole number."""
    numbers = np.rint(vectors * SCALE).astype(np.int64)
    header = [name, *(f"e_{i}" for i in range(1, vectors.shape[1] + 1))]
    write(path, header, [[id_, *row] for id_, row in zip(ids, numbers.tolist(), strict=True)])


def build(out: Path, server: Path, downloads: Path) -> None:
    archive = download(DATASET, DATASET_SHA256, downloads / "multidoc2dial.zip")
    model = download(MODEL, MODEL_SHA256, downloads / "nomic-embed-text-v1.5.Q8_0.gguf")
    with zipfile.ZipFile(archive) as packed:

        def read(name: str) -> dict:
            return json.loads(packed.read(f"multidoc2dial/{name}").decode("utf-8"))

        docs = read("multidoc2dial_doc.json")["doc_data"]
        splits = ("train", "validation")
        dialogues = {
            split: read(f"multidoc2dial_dial_{split}.json")["dial_data"] for split in splits
        }
    pages: dict[str, dict] = {}
    for domain in DOMAINS:
        for number, (doc_id, doc) in enumerate(docs[domain].items(), start=1):
            text = page_text(doc["doc_html_raw"])
            pages[doc_id] = {
                "page": f"{domain}-{number}",
                "domain": domain,
                "title": re.sub(r"#\d+$", "", doc["title"]),
                "text": text,
                "move": mover(doc["doc_text"], text),
                "spans": doc["spans"],
            }
    passages: list[dict] = []
    for doc_id, page in pages.items():
        for start, end in passages_of(page["text"]):
            number = len(passages) + 1
            text = page["text"][start:end]
            passages.append(
                {"passage": f"p{number}", "doc": doc_id, "start": start, "end": end, "text": text}
            )
    found: dict[str, list[dict]] = {"train": [], "validation": []}
    for split, by_domain in dialogues.items():
        for domain in DOMAINS:
            for dialogue in by_domain.get(domain, []):
                turns = dialogue["turns"]
                if len(turns) < 2 or (turns[0]["role"], turns[1]["role"]) != ("user", "agent"):
                    continue
                doc_id = turns[0]["references"][0]["doc_id"]
                page = pages[doc_id]
                parts = set()
                for reference in turns[1]["references"]:
                    if reference["label"] != "solution" or reference["doc_id"] != doc_id:
                        continue
                    span = page["spans"][reference["id_sp"]]
                    start, end, share = page["move"](span["start_sp"], span["end_sp"])
                    if share >= MOVED:
                        parts.add((start, end))
                if parts:
                    question = " ".join(turns[0]["utterance"].split())
                    found[split].append({"doc": doc_id, "text": question, "parts": parts})
    rng = np.random.default_rng(0)
    drawn = sorted(rng.choice(len(found["train"]), VALIDATION, replace=False).tolist())
    questions = [{**found["train"][i], "set": "validation"} for i in drawn]
    questions += [{**question, "set": "test"} for question in found["validation"]]
    by_text: dict[str, list[int]] = {}
    for index, passage in enumerate(passages):
        by_text.setdefault(passage["text"], []).append(index)
    relevant: list[list[object]] = []
    for number, question in enumerate(questions, start=1):
        question["question"] = f"q{number}"
        holding = {
            passage["text"]
            for passage in passages
            if passage["doc"] == question["doc"]
            and any(
                min(e, passage["end"]) - max(s, passage["start"]) >= HELD * (e - s)
                for s, e in question["parts"]
            )
        }
        same = sorted(index for text in holding for index in by_text[text])
        relevant += [[question["question"], passages[index]["passage"]] for index in same]
    rows: list[list[object]] = []
    for passage in passages:
        page = pages[passage["doc"]]
        rows.append(
            [passage["passage"], page["page"], page["domain"], page["title"], passage["text"]]
        )
    write(out / "passages.csv", ["passage", "page", "domain", "title", "text"], rows)
    rows = []
    for question in questions:
        page = pages[question["doc"]]
        rows.append(
            [question["question"], question["set"], page["page"], page["domain"], question["text"]]
        )
    write(out / "questions.csv", ["question", "set", "page", "domain", "text"], rows)
    write(out / "relevant.csv", ["question", "passage"], relevant)
    validation = [question for question in questions if question["set"] == "validation"]
    with served(server, model, downloads / "llama-server.log") as embed:
        passage_vectors = np.array([embed(DOCUMENT + passage["text"]) for passage in passages])
        question_vectors = np.array([embed(QUERY + question["text"]) for question in questions])
        as_passages = np.array([embed(DOCUMENT + question["text"]) for question in validation])
    ids = [passage["passage"] for passage in passages]
    write_vectors(out / "passage-vectors.csv", "passage", ids, passage_vectors)
    ids = [question["question"] for question in questions]
    write_vectors(out / "question-vectors.csv", "question", ids, question_vectors)
    ids = [question["question"] for question in validation]
    write_vectors(out / "question-vectors-as-passages.csv", "question", ids, as_passages)


if __name__ == "__main__":
    out, server = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 3:
        build(out, server, Path(sys.argv[3]))
    else:
        with tempfile.TemporaryDirectory() as downloads:
            build(out, server, Path(downloads))

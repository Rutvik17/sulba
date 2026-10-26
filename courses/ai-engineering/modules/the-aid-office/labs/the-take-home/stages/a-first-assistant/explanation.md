```python
import csv
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

import httpx

MODEL = "Qwen3.5-0.8B"
WORDS = 200
BEST = 5
STAFF = "I'll pass your question to the aid office's staff, who will reply by email."
INSTRUCTIONS = (
    "You answer students' questions for Harbor College's aid office, from the numbered "
    "passages of Federal Student Aid's pages that come with each question, and from nothing "
    "else. Cite each passage you use by its number in brackets, such as [2]. If the passages "
    "don't answer the question, reply only: I don't know."
)


@dataclass(frozen=True)
class Passage:
    page: str
    title: str
    text: str


@dataclass(frozen=True)
class Answer:
    text: str
    pages: list[str]
    to_staff: bool


def passages(path):
    """The pages' passages, in order: each page's blocks, which a blank line divides, joined
    until another would take a passage past WORDS words."""
    found = []
    with open(path, encoding="utf-8", newline="") as file:
        for page in csv.DictReader(file):
            joined, count = [], 0
            for block in page["text"].split("\n\n"):
                size = len(block.split())
                if joined and count + size > WORDS:
                    text = "\n\n".join(joined)
                    found.append(Passage(page["page"], page["title"], text))
                    joined, count = [], 0
                joined.append(block)
                count += size
            if joined:
                text = "\n\n".join(joined)
                found.append(Passage(page["page"], page["title"], text))
    return found


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


class Search:
    """BM25 over the passages' titles and texts, with an index of where each word appears."""

    def __init__(self, passages, k1=1.2, b=0.75):
        self.passages = passages
        self.where = defaultdict(list)
        lengths = []
        for place, passage in enumerate(passages):
            counts = Counter(words(f"{passage.title} {passage.text}"))
            lengths.append(sum(counts.values()))
            for word, count in counts.items():
                self.where[word].append((place, count))
        mean = sum(lengths) / len(passages)
        self.norms = [k1 * (1 - b + b * length / mean) for length in lengths]
        n = len(passages)
        self.idf = {
            word: math.log(1 + (n - len(held) + 0.5) / (len(held) + 0.5))
            for word, held in self.where.items()
        }
        self.k1 = k1

    def best(self, question, k):
        """The k passages that best answer the question, best first, none that shares no word
        with it."""
        scores = defaultdict(float)
        for word in set(words(question)):
            for place, count in self.where.get(word, []):
                tf = count * (self.k1 + 1) / (count + self.norms[place])
                scores[place] += self.idf[word] * tf
        ranked = sorted(scores, key=lambda place: (-scores[place], place))
        return [self.passages[place] for place in ranked[:k]]


def answer(client, search, question):
    """The model's answer from the question's best passages, with the pages it cites, or the
    question passed to staff when there's nothing to answer from, the model can't answer, or its
    reply cites nothing."""
    found = search.best(question, BEST)
    if not found:
        return Answer(STAFF, [], True)
    numbered = "\n\n".join(
        f"[{number}] {passage.title}\n{passage.text}"
        for number, passage in enumerate(found, start=1)
    )
    messages = [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": f"{numbered}\n\nQuestion: {question}"},
    ]
    body = {"model": MODEL, "messages": messages, "max_completion_tokens": 400}
    try:
        response = client.post("/chat/completions", json=body)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"] or ""
    except httpx.HTTPError, KeyError, IndexError, ValueError:
        return Answer(STAFF, [], True)
    pages = []
    for cited in re.findall(r"\[(\d+)\]", reply):
        number = int(cited)
        if 1 <= number <= len(found) and found[number - 1].page not in pages:
            pages.append(found[number - 1].page)
    if not pages or reply.strip().rstrip(".").lower() == "i don't know":
        return Answer(STAFF, [], True)
    return Answer(reply.strip(), pages, False)
```


The search is BM25 over each passage's title and text, with `$k_1 = 1.2$` and `$b = 0.75$`. Built once, it keeps for each word the passages that hold it and how often, so a question scores only the passages that share one of its words, and a passage that shares none is never given. For the office's {% $fig.questions %} questions, the page that answers one is among the pages of its {% $fig.best %} best passages for {% $fig.found %} of them, and its best passage's page for {% $fig.first %}.

Opening questions are often vague, such as "I have a question about the FAFSA program.", and the search can only find a page for words the question holds. That's why answers that cite nothing go to staff: an answer that names no passage may not come from the pages at all.

`answer` numbers the passages so that the reply can cite them, and reads the pages from the numbers, never from the model's words. Every way the model can fail, an error, a dropped connection or a reply that doesn't come, raises an `httpx.HTTPError`, and each sends the question to staff rather than the student an error.

The full build goes on from here: a search by meaning beside the words, measured on the office's questions; the student's own aid record through the office's systems, for the student signed in; an eval suite; and the assistant shipped on the office's own server, with nothing leaving it.

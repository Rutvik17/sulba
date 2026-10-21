# /// script
# requires-python = "==3.14.2"
# dependencies = ["jinja2==3.1.6", "numpy==2.5.4", "scikit-learn==1.9.1", "transformers==5.20.1"]
# [tool.uv]
# exclude-newer = "2026-10-19T00:00:00Z"
# ///
"""Records how transformers renders Granite Guardian 3.1 2B's prompt, and how scikit-learn
scores a grader against people's labels, for the lab's tests. Their dependencies are those
released before 19 October 2026.

prompts.json holds the prompt transformers renders with IBM's tokenizer for Granite Guardian
3.1 2B, at revision 8114548, asking whether a reply keeps to its context, for made-up contexts
and replies and for the first of BEGIN's in the lab's data, each with the date the template
writes as today's. make.py first checks that the tokenizer's chat template is the one in the
lab's `tokenizer_config.json`.

agreement.json holds scikit-learn's accuracy, Cohen's kappa and ROC AUC for made-up labels,
1 where people found a reply says something its context doesn't, with a grader's scores and
its verdicts at a threshold.

    uv run make.py <folder to write in> <folder of the lab's data>
"""

import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, cohen_kappa_score, roc_auc_score
from transformers import AutoTokenizer

NAME = "ibm-granite/granite-guardian-3.1-2b"
REVISION = "81145486e85c6c82c01e759c0356d9d6da4d21a5"
DAYS = ["October 20, 2026", "January 02, 2027"]
MADE_UP = [
    ("We open at 9 on weekdays.", "We open at 9."),
    (
        "Renew your license online.\n\n- Have your card ready",
        "You can renew it online.",
    ),
    ('Quotes "like this" and {braces} stay as they are.', '{braces} and "quotes".'),
    ("[p12] Title\nA passage with a name.", "It has a name [p12]."),
]
BEGIN = 5
CASES = 40


def prompts(data: Path) -> list[dict[str, str]]:
    tokenizer = AutoTokenizer.from_pretrained(NAME, revision=REVISION)
    config = json.loads((data / "tokenizer_config.json").read_text(encoding="utf-8"))
    if tokenizer.chat_template != config["chat_template"]:
        raise SystemExit("The tokenizer's chat template isn't the lab's.")
    with open(data / "begin.csv", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))[:BEGIN]
    pairs = MADE_UP + [(row["context"], row["reply"]) for row in rows]
    out = []
    for number, (context, reply) in enumerate(pairs):
        today = DAYS[number % len(DAYS)]
        messages = [
            {"role": "context", "content": context},
            {"role": "assistant", "content": reply},
        ]
        # The template writes today's date with strftime_now, which a keyword argument
        # passes in place of transformers' own.
        text = tokenizer.apply_chat_template(
            messages,
            guardian_config={"risk_name": "groundedness"},
            tokenize=False,
            add_generation_prompt=True,
            strftime_now=lambda _, today=today: today,
        )
        out.append({"context": context, "reply": reply, "today": today, "prompt": text})
    return out


def agreement() -> list[dict[str, object]]:
    rng = np.random.default_rng(3)
    cases = []
    for number in range(CASES):
        n = int(rng.integers(8, 120))
        labels = rng.integers(0, 2, size=n)
        labels[:2] = [0, 1]
        noise = rng.normal(0, 0.25 + number / CASES, size=n)
        scores = np.clip(labels * 0.5 + 0.25 + noise, 0, 1)
        if number % 3 == 0:
            scores = np.round(scores, 1)
        threshold = float(rng.choice([0.25, 0.5, 0.6]))
        verdicts = (scores >= threshold).astype(int)
        cases.append(
            {
                "labels": labels.tolist(),
                "scores": scores.tolist(),
                "threshold": threshold,
                "verdicts": verdicts.tolist(),
                "accuracy": float(accuracy_score(labels, verdicts)),
                "kappa": float(cohen_kappa_score(labels, verdicts)),
                "auc": float(roc_auc_score(labels, scores)),
            }
        )
    return cases


def make(folder: Path, data: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name, content in (
        ("prompts.json", {"cases": prompts(data)}),
        ("agreement.json", {"cases": agreement()}),
    ):
        with open(folder / name, "w", encoding="utf-8", newline="\n") as file:
            json.dump(content, file, indent=1, ensure_ascii=False)
            file.write("\n")


if __name__ == "__main__":
    here = Path(__file__).parent
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else here
    data = Path(sys.argv[2]) if len(sys.argv) > 2 else here.parent / "data"
    make(folder, data)

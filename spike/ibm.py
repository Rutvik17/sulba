# /// script
# requires-python = "==3.14.2"
# dependencies = ["jinja2==3.1.6", "torch==2.14.1", "transformers==5.20.1"]
#
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
#
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
# ///
"""Spike: IBM's Granite Guardian 3.1 2B, through transformers in bfloat16 as its model card runs
it, on the first items of a file guardian.py grades, to check the GGUF against it: the summed
probabilities of "Yes" and "No" among the 20 likeliest first tokens, as the card reads them.

    uv run spike/ibm.py <items> <count> <file to write>
"""

import csv
import math
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "datasets"))
import guardian  # noqa: E402

REVISION = "81145486e85c6c82c01e759c0356d9d6da4d21a5"
NAME = "ibm-granite/granite-guardian-3.1-2b"
csv.field_size_limit(1 << 24)
items = list(csv.DictReader(open(sys.argv[1], encoding="utf-8", newline="")))[: int(sys.argv[2])]
tokenizer = AutoTokenizer.from_pretrained(NAME, revision=REVISION)
model = AutoModelForCausalLM.from_pretrained(NAME, revision=REVISION, dtype=torch.bfloat16)
model.eval()
rows = []
for item in items:
    messages = [
        {"role": "context", "content": item["context"]},
        {"role": "assistant", "content": item["reply"]},
    ]
    text = tokenizer.apply_chat_template(
        messages, guardian_config={"risk_name": "groundedness"}, tokenize=False,
        add_generation_prompt=True,
    )
    text = text.replace(__import__("time").strftime("%B %d, %Y"), guardian.TODAY)
    ids = tokenizer(text, return_tensors="pt", add_special_tokens=False).input_ids
    with torch.no_grad():
        logits = model(ids).logits[0, -1].float()
    logprobs = torch.log_softmax(logits, dim=-1)
    top = torch.topk(logprobs, guardian.LIKELIEST)
    sums = {"yes": 0.0, "no": 0.0}
    for value, index in zip(top.values.tolist(), top.indices.tolist(), strict=True):
        word = tokenizer.convert_ids_to_tokens(index).strip().lower()
        if word in sums:
            sums[word] += math.exp(value)
    rows.append([item["item"], sums["yes"], sums["no"]])
    print(item["item"], sums, flush=True)
with open(sys.argv[3], "w", encoding="utf-8", newline="\n") as file:
    writer = csv.writer(file, lineterminator="\n")
    writer.writerow(["item", "yes", "no"])
    writer.writerows(rows)

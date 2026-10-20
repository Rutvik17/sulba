# /// script
# requires-python = "==3.14.2"
# dependencies = ["jinja2==3.1.6"]
# ///
"""Records how Granite Guardian 3.1 2B judges whether replies keep to what they were given: the
probabilities it gives the answer "Yes", that a reply says something its context doesn't, and
the answer "No".

The items are the rows of a CSV file with an `item`, its `context` and its `reply`. Each prompt
is the model's chat template, from IBM's tokenizer configuration at revision 8114548, rendered
with jinja2 as transformers renders a chat template: the risk `groundedness`, the context as a
message of the role `context` and the reply as the assistant's, with the prompt for the answer,
and 20 October 2026 as today's date. llama.cpp's llama-server b11734 runs the model at 8 bits,
from mrutkows's GGUF repository at revision 1f4034a, with 4,096 tokens of context, and its
completions endpoint gives the log probabilities of the 20 likeliest first tokens of the answer.
As IBM's model card reads them, a token is "Yes" or "No" when it is one of them with the spaces
around it taken off and in any case, and each answer's probability is the sum of its tokens'.
The file written holds each item beside the two sums.

    uv run tools/datasets/guardian.py <items> <llama-server> <file to write> \\
        [<shard>/<shards>] [<downloads>]

<llama-server> is llama.cpp's server, release b11734, such as the one `uv run sulba.py model`
fetches into `sulba` in the cache folder. With a shard, such as 3/20, the script grades the third
of 20 runs of items in order, so that the shards' files, joined in order, are the whole. The
model comes to 2.7 GB. Given a folder of downloads, the script keeps it there for the next run;
without one, it downloads it to a temporary folder.
"""

import csv
import json
import math
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import jinja2
import jinja2.ext
import jinja2.sandbox
import llama

# Granite Guardian 3.1 2B at 8 bits, from mrutkows's GGUF repository at revision 1f4034a, and
# IBM's tokenizer configuration, which holds its chat template, at revision 8114548.
MODEL = (
    "https://huggingface.co/mrutkows/granite-guardian-3.1-2b-GGUF/resolve/"
    "1f4034aca92fe0094b68581bf2d0222ad0b7b816/granite-guardian-3.1-2b-Q8_0.gguf"
)
MODEL_SHA256 = "6cf7bc53013e0c077a74e3ea29383f520dfed34125adc467e8a645374e93c6cd"
TOKENIZER = (
    "https://huggingface.co/ibm-granite/granite-guardian-3.1-2b/resolve/"
    "81145486e85c6c82c01e759c0356d9d6da4d21a5/tokenizer_config.json"
)
TOKENIZER_SHA256 = "c2b3840f831434d583a4b0c804fc4a217141161c6008017fb89eba212d2e6d87"
OPTIONS = ["--ctx-size", "4096"]
TODAY = "October 20, 2026"
# How many of the likeliest first tokens are read, as IBM's model card reads them.
LIKELIEST = 20


def prompter(tokenizer: Path) -> Callable[[str, str], str]:
    """A function that gives the prompt that asks the model whether a reply keeps to its
    context, rendered from the chat template as transformers renders one."""

    def refuse(message: str) -> None:
        raise ValueError(message)

    environment = jinja2.sandbox.ImmutableSandboxedEnvironment(
        trim_blocks=True, lstrip_blocks=True, extensions=[jinja2.ext.loopcontrols]
    )
    environment.globals["raise_exception"] = refuse
    environment.globals["strftime_now"] = lambda _: TODAY
    with open(tokenizer, encoding="utf-8") as file:
        template = environment.from_string(json.load(file)["chat_template"])

    def prompt(context: str, reply: str) -> str:
        messages = [
            {"role": "context", "content": context},
            {"role": "assistant", "content": reply},
        ]
        return template.render(
            messages=messages,
            guardian_config={"risk_name": "groundedness"},
            add_generation_prompt=True,
        )

    return prompt


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def record(items: Path, server: Path, out: Path, shard: str, downloads: Path) -> None:
    model = llama.download(MODEL, MODEL_SHA256, downloads / "granite-guardian-3.1-2b-Q8_0.gguf")
    tokenizer = llama.download(TOKENIZER, TOKENIZER_SHA256, downloads / "tokenizer_config.json")
    prompt = prompter(tokenizer)
    asked = read(items)
    part, parts = (int(number) for number in shard.split("/"))
    size = -(-len(asked) // parts)
    asked = asked[(part - 1) * size : part * size]
    rows: list[list[object]] = []
    with llama.serving(server, model, OPTIONS, downloads / "llama-server.log") as post:
        for done, item in enumerate(asked, start=1):
            body = {
                "prompt": prompt(item["context"], item["reply"]),
                "max_tokens": 1,
                "temperature": 0,
                "logprobs": LIKELIEST,
            }
            reply = post("/v1/completions", body)
            likeliest = reply["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
            sums = {"yes": 0.0, "no": 0.0}
            for token in likeliest:
                word = token["token"].strip().lower()
                if word in sums:
                    sums[word] += math.exp(token["logprob"])
            rows.append([item["item"], sums["yes"], sums["no"]])
            if done % 50 == 0 or done == len(asked):
                print(f"{done} of {len(asked)} items", file=sys.stderr, flush=True)
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["item", "yes", "no"])
        writer.writerows(rows)


if __name__ == "__main__":
    csv.field_size_limit(1 << 24)
    items, server, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    shard = sys.argv[4] if len(sys.argv) > 4 else "1/1"
    if len(sys.argv) > 5:
        record(items, server, out, shard, Path(sys.argv[5]))
    else:
        with tempfile.TemporaryDirectory() as downloads:
            record(items, server, out, shard, Path(downloads))

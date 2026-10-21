"""Granite Guardian's verdict on whether a reply keeps to its passages."""

import json
import math
from pathlib import Path

import httpx
import jinja2
import jinja2.ext
import jinja2.sandbox

# How many of the likeliest first tokens the server gives, as IBM's model card reads them.
LIKELIEST = 20


def template(path: Path) -> jinja2.Template:
    """The chat template in a tokenizer's configuration, compiled as transformers compiles
    one."""

    def refuse(message: str) -> None:
        raise jinja2.TemplateError(message)

    environment = jinja2.sandbox.ImmutableSandboxedEnvironment(
        trim_blocks=True, lstrip_blocks=True, extensions=[jinja2.ext.loopcontrols]
    )
    environment.globals["raise_exception"] = refuse
    config = json.loads(path.read_text(encoding="utf-8"))
    return environment.from_string(config["chat_template"])


def prompt(chat: jinja2.Template, context: str, reply: str, today: str) -> str:
    """The prompt that asks whether the reply says anything its context doesn't, with the
    date the template writes as today's."""
    messages = [
        {"role": "context", "content": context},
        {"role": "assistant", "content": reply},
    ]
    return chat.render(
        messages=messages,
        guardian_config={"risk_name": "groundedness"},
        add_generation_prompt=True,
        strftime_now=lambda _: today,
    )


def risk(client: httpx.Client, text: str) -> float:
    """The probability the grader gives "Yes", that the reply says something its context
    doesn't, over its probability of "Yes" or "No"."""
    body = {
        "model": "Granite-Guardian-3.1-2B",
        "prompt": text,
        "max_tokens": 1,
        "temperature": 0,
        "logprobs": LIKELIEST,
    }
    reply = client.post("/completions", json=body)
    reply.raise_for_status()
    likeliest = reply.json()["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    sums = {"yes": 0.0, "no": 0.0}
    for token in likeliest:
        word = token["token"].strip().lower()
        if word in sums:
            sums[word] += math.exp(token["logprob"])
    return sums["yes"] / (sums["yes"] + sums["no"])

# /// script
# requires-python = "==3.14.2"
# dependencies = [
#   "jinja2==3.1.6",
#   "tokenizers==0.23.3",
#   "transformers==5.18.0",
# ]
# ///
"""Records the tokens Qwen3.5-0.8B reads for the shop's conversations, for the lab's tests.

transformers' apply_chat_template writes each conversation with the model's own chat template,
from its chat_template.jinja, and the generation prompt that asks for the assistant's reply,
without thinking, as llama.cpp's server writes it with reasoning off. The model's tokenizer.json
turns the text into tokens.

tokens.json holds each conversation with its tokens, and for the long conversation, the number
of tokens its turns from each one on take, with its system message and without it, a turn being
a customer's message with the replies that follow it.

    uv run make.py <folder to write in> <folder of the lab's data>
"""

import json
import sys
from pathlib import Path

import tokenizers
import transformers
from transformers import PreTrainedTokenizerFast

SYSTEM = {
    "role": "system",
    "content": "You answer customers' questions for a bicycle repair shop, in a sentence or two.",
}
CONVERSATIONS = [
    [{"role": "user", "content": "When do you open on Saturday?"}],
    [SYSTEM, {"role": "user", "content": "How much is a puncture repair?"}],
    [
        SYSTEM,
        {"role": "user", "content": "Do you fix e-bikes?"},
        {
            "role": "assistant",
            "content": "Yes, we service most e-bikes, but not their batteries.",
        },
        {"role": "user", "content": "Can I bring mine in on Monday?"},
    ],
    [
        SYSTEM,
        {"role": "user", "content": "  My chain keeps slipping.  \n"},
        {
            "role": "assistant",
            "content": "\nThat often means a worn chain or cassette. Bring it in and we'll check it. ",
        },
        {"role": "user", "content": "Great, thanks! 🚲"},
    ],
    [
        {
            "role": "user",
            "content": "Ça coûte combien, un réglage des freins ? Und für zwei Räder?",
        }
    ],
]
LONG = [
    SYSTEM,
    {"role": "user", "content": "Hi, my rear brake squeals when I stop."},
    {
        "role": "assistant",
        "content": "That's usually dirty or glazed pads. Cleaning them often fixes it.",
    },
    {"role": "user", "content": "I cleaned them and it still squeals."},
    {
        "role": "assistant",
        "content": "Then the pads may need replacing. We can fit new ones while you wait.",
    },
    {"role": "user", "content": "How much would that be?"},
    {"role": "assistant", "content": "New pads for one brake are £18, fitted."},
    {"role": "user", "content": "And for both brakes?"},
    {"role": "assistant", "content": "Both would be £32, fitted."},
    {"role": "user", "content": "Do you have time this afternoon?"},
    {"role": "assistant", "content": "We have a slot at 3pm today."},
    {"role": "user", "content": "Can my son come instead of me?"},
    {"role": "assistant", "content": "Of course. He only needs to bring the bike."},
    {"role": "user", "content": "Do you take cards?"},
    {"role": "assistant", "content": "Yes, cards and contactless."},
    {"role": "user", "content": "Is there parking nearby?"},
    {"role": "assistant", "content": "There's a car park two minutes away on foot."},
    {"role": "user", "content": "Great. Can you also check the gears while it's in?"},
]


def turns(messages):
    """The index of each turn's first message: each customer's message after the system's."""
    return [
        index for index, message in enumerate(messages) if message["role"] == "user"
    ]


def main(folder, data):
    tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(data / "tokenizer.json"))
    template = (data / "chat_template.jinja").read_text(encoding="utf-8")

    def tokens(messages):
        written = tokenizer.apply_chat_template(
            messages, chat_template=template, tokenize=True, add_generation_prompt=True
        )
        return list(written["input_ids"] if hasattr(written, "keys") else written)

    recording = {
        "transformers": transformers.__version__,
        "tokenizers": tokenizers.__version__,
        "conversations": [
            {"messages": messages, "tokens": tokens(messages)}
            for messages in CONVERSATIONS
        ],
        "long": {
            "messages": LONG,
            "counts": [len(tokens([SYSTEM, *LONG[start:]])) for start in turns(LONG)],
            "without_system": [len(tokens(LONG[start:])) for start in turns(LONG)],
        },
    }
    (folder / "tokens.json").write_text(
        json.dumps(recording, indent=1, ensure_ascii=False) + "\n"
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))

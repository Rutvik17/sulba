from tokenizers import Tokenizer

TOKENIZER = "data/tokenizer.json"
# The tokens llama.cpp's server reads at once, as sulba.py runs it, and the context Qwen3.5-0.8B
# was trained for, from its config.json at the lab's revision.
WINDOW, TRAINED = 4096, 262144
QUESTION = "When do you open on Saturday?"
SYSTEM = {
    "role": "system",
    "content": "You answer customers' questions for a bicycle repair shop, in a sentence or two.",
}
# The long conversation of the lab's references, as the shop's assistant would send it.
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


def prompt(messages):
    text = "".join(
        f"<|im_start|>{message['role']}\n{message['content'].strip()}<|im_end|>\n"
        for message in messages
    )
    return text + "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def figures():
    tokenizer = Tokenizer.from_file(TOKENIZER)

    def count(messages):
        return len(tokenizer.encode(prompt(messages)).ids)

    words = len(tokenizer.encode(QUESTION).ids)
    asked = count([{"role": "user", "content": QUESTION}])
    questions = [
        index for index, message in enumerate(LONG) if message["role"] == "user"
    ]
    # Each question is sent with the conversation before it.
    read = sum(count(LONG[: index + 1]) for index in questions)
    return {
        "window": f"{WINDOW:,}",
        "trained": f"{TRAINED:,}",
        "question_tokens": str(words),
        "asked_tokens": str(asked),
        "template_tokens": str(asked - words),
        "questions": str(len(questions)),
        "long_tokens": str(count(LONG)),
        "long_read": f"{read:,}",
    }

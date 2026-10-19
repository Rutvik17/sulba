from tokenizers import Tokenizer

TOKENIZER = "data/tokenizer.json"
INSTRUCTIONS = (
    "You answer customers' questions for a bicycle repair shop, in a sentence or two."
)
WINDOW, REPLY = 4096, 256
# The conversation of the check on the reply's room: the questions, and each reply.
QUESTIONS = 40
LONG_REPLY = "Bring it in and we'll take a look at it for you. " * 20


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

    def fit(messages, reply):
        starts = [
            index for index, message in enumerate(messages) if message["role"] == "user"
        ]
        for start in starts:
            kept = messages[:1] + messages[start:]
            if count(kept) + reply <= WINDOW:
                return kept
        raise ValueError

    # The assistant's code: as much of the conversation as the window holds, with no room kept.
    messages = [{"role": "system", "content": INSTRUCTIONS}]
    for number in range(QUESTIONS):
        messages.append(
            {"role": "user", "content": f"Question {number}: can you look at my gears?"}
        )
        sent = fit(messages, 0)
        messages.append({"role": "assistant", "content": LONG_REPLY})
    last = count(sent)
    assert WINDOW - last < REPLY
    return {
        "questions": str(QUESTIONS),
        "prompt": f"{last:,}",
        "window": f"{WINDOW:,}",
        "left": str(WINDOW - last),
        "reply": str(REPLY),
    }

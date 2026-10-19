"""The shop's assistant: a customer's conversation, sent to the model within its window."""

import httpx
from tokenizers import Tokenizer

from chat import ModelError, ask
from window import fit

INSTRUCTIONS = (
    "You answer customers' questions for a bicycle repair shop, in a sentence or two."
)
# The tokens the model's server holds, and the most a reply may take.
WINDOW, REPLY = 4096, 256
SORRY = "Sorry, I can't answer that right now. Please call the shop."


class Assistant:
    """One customer's conversation with the shop's assistant."""

    def __init__(self, client: httpx.Client, tokenizer: Tokenizer) -> None:
        self.client = client
        self.tokenizer = tokenizer
        self.messages = [{"role": "system", "content": INSTRUCTIONS}]

    def answer(self, question: str) -> str:
        """The model's answer to the customer's question, or SORRY when it has none to give."""
        self.messages.append({"role": "user", "content": question})
        sent = fit(self.tokenizer, self.messages, WINDOW, REPLY)
        try:
            reply = ask(self.client, sent, REPLY)
        except ModelError:
            return SORRY
        if reply.finish_reason != "stop":
            return SORRY
        self.messages.append({"role": "assistant", "content": reply.text})
        return reply.text

from collections.abc import Iterator

from openai import OpenAI


def ask(client: OpenAI, question: str) -> str:
    reply = client.chat.completions.create(
        model="shop", messages=[{"role": "user", "content": question}], temperature=0
    )
    return reply.choices[0].message.content or ""


def pieces(client: OpenAI, question: str) -> Iterator[str]:
    stream = client.chat.completions.create(
        model="shop", messages=[{"role": "user", "content": question}], stream=True
    )
    for chunk in stream:
        for choice in chunk.choices:
            if choice.delta.content:
                yield choice.delta.content

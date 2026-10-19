import json

import httpx


def ask(client: httpx.Client, question: str) -> str:
    response = client.post(
        "/chat/completions",
        json={"model": "shop", "messages": [{"role": "user", "content": question}]},
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def events(client: httpx.Client, question: str) -> list[dict | str]:
    """Each server-sent event of a streamed reply: its JSON, or the text that ends the stream."""
    body = {
        "model": "shop",
        "messages": [{"role": "user", "content": question}],
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    found: list[dict | str] = []
    with client.stream("POST", "/chat/completions", json=body) as response:
        for line in response.iter_lines():
            if line.startswith("data: "):
                data = line.removeprefix("data: ")
                found.append(data if data == "[DONE]" else json.loads(data))
    return found


async def ask_soon(client: httpx.AsyncClient, question: str) -> str:
    response = await client.post(
        "/chat/completions",
        json={"model": "shop", "messages": [{"role": "user", "content": question}]},
        timeout=2,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def ask_until_answered(client: httpx.Client, question: str) -> str:
    """Asks again after any error at all, which hides the errors it shouldn't."""
    while True:
        try:
            return ask(client, question)
        except Exception:
            continue

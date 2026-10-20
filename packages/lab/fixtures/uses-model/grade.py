import math

import httpx


def grounded(client: httpx.Client, prompt: str) -> float:
    """The probability that the grader answers No, out of its probabilities of Yes and No for
    its first token."""
    body = {"model": "grader", "prompt": prompt, "max_tokens": 1, "temperature": 0, "logprobs": 5}
    response = client.post("/completions", json=body)
    response.raise_for_status()
    [first] = response.json()["choices"][0]["logprobs"]["content"]
    weights = {item["token"]: math.exp(item["logprob"]) for item in first["top_logprobs"]}
    return weights.get("No", 0.0) / (weights.get("Yes", 0.0) + weights.get("No", 0.0))

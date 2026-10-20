"""Spike: one llama-server in router mode serving a chat model, an embedding model and a reranker
by name, as a lab's `uv run sulba.py model` would, before the Retrieval module's decision record.

On macOS the embedding model and the reranker run on the CPU (`device = none`) and the chat model
on the GPU. Prints what it found as JSON, and into the job's summary on GitHub Actions.

    uv run --no-project --python 3.14 tools/spike/router.py <folder for downloads>
"""

import json
import math
import os
import platform
import sys
import time
import urllib.error
from pathlib import Path

from models import BUILDS, HF, MODELS, PASSAGES, QUESTIONS, RELEASE, TAG, call, fetched, timed
from models import cosine, serve, unpacked

CHAT = {
    "url": f"{HF}/ggml-org/Qwen3.5-0.8B-GGUF/resolve/"
    "8fea620810c4afa23dd6443f999a48574c1611a3/Qwen3.5-0.8B-Q8_0.gguf",
    "size": 833592096,
    "sha256": "37ae482d336108d23516fa35e8e0c4126688d81018b87178a18d752a1357814f",
}


def main(folder):
    sys.stdout.reconfigure(encoding="utf-8")
    folder.mkdir(parents=True, exist_ok=True)
    found = {
        "system": f"{platform.system()} {platform.release()} {platform.machine()}",
        "cpus": os.cpu_count(),
    }
    build, size, sha256 = BUILDS[(platform.system(), platform.machine())]
    archive = fetched(f"{RELEASE}/llama-{TAG}-{build}", size, sha256, folder / f"llama-{build}")
    server = unpacked(archive, folder / "llama")
    chat = fetched(CHAT["url"], CHAT["size"], CHAT["sha256"], folder / "Qwen3.5-0.8B.gguf")
    nomic = MODELS["nomic-embed-text-v1.5"]
    embed = fetched(nomic["url"], nomic["size"], nomic["sha256"], folder / "nomic.gguf")
    qwen = MODELS["Qwen3-Reranker-0.6B"]
    rerank = fetched(qwen["url"], qwen["size"], qwen["sha256"], folder / "reranker.gguf")
    cpu = "device = none\n" if platform.system() == "Darwin" else ""
    preset = folder / "models.ini"
    preset.write_text(
        "version = 1\n\n"
        f"[Qwen3.5-0.8B]\nmodel = {chat.resolve().as_posix()}\nc = 4096\nreasoning = off\n\n"
        f"[nomic-embed-text-v1.5]\nmodel = {embed.resolve().as_posix()}\nembeddings = true\n"
        f"c = 2048\nbatch-size = 2048\nubatch-size = 2048\n{cpu}\n"
        f"[Qwen3-Reranker-0.6B]\nmodel = {rerank.resolve().as_posix()}\nrerank = true\n"
        f"c = 4096\nbatch-size = 2048\nubatch-size = 2048\n{cpu}",
        encoding="utf-8",
    )
    found["preset"] = preset.read_text(encoding="utf-8").replace(folder.resolve().as_posix(), "~")
    process, found["ready_s"] = serve(
        server, None, ["--models-preset", str(preset)], folder / "router.log"
    )
    try:
        found["models"] = [m["id"] for m in call("/v1/models")["data"]]
        reply, found["chat_first_s"] = timed(
            "/v1/chat/completions",
            {
                "model": "Qwen3.5-0.8B",
                "messages": [{"role": "user", "content": "Name one part of a bicycle."}],
                "max_completion_tokens": 30,
            },
        )
        found["chat_reply"] = reply["choices"][0]["message"]["content"][:200]
        found["chat_usage"] = reply.get("usage")
        documents = [f"search_document: {p}" for p in PASSAGES]
        reply, found["embed_first_s"] = timed(
            "/v1/embeddings", {"model": "nomic-embed-text-v1.5", "input": documents}
        )
        vectors = [d["embedding"] for d in sorted(reply["data"], key=lambda d: d["index"])]
        found["dimensions"] = len(vectors[0])
        found["first_numbers"] = [round(x, 6) for x in vectors[0][:6]]
        ranks = []
        for question, answer in QUESTIONS:
            reply = call(
                "/v1/embeddings",
                {"model": "nomic-embed-text-v1.5", "input": f"search_query: {question}"},
            )
            query = reply["data"][0]["embedding"]
            order = sorted(range(len(vectors)), key=lambda i: -cosine(query, vectors[i]))
            ranks.append(order.index(answer) + 1)
        found["embed_answer_ranks"] = ranks
        # A passage of about 1,500 tokens, near the 2,048 that one batch holds.
        long = "search_document: " + " ".join(PASSAGES * 3)
        reply, found["embed_long_s"] = timed(
            "/v1/embeddings", {"model": "nomic-embed-text-v1.5", "input": long}
        )
        found["embed_long_tokens"] = reply.get("usage", {}).get("prompt_tokens")
        reply, found["rerank_first_s"] = timed(
            "/v1/rerank",
            {"model": "Qwen3-Reranker-0.6B", "query": QUESTIONS[0][0], "documents": PASSAGES},
        )
        found["rerank_top"] = max(reply["results"], key=lambda r: r["relevance_score"])["index"]
        reply, found["rerank_second_s"] = timed(
            "/v1/rerank",
            {"model": "Qwen3-Reranker-0.6B", "query": QUESTIONS[1][0], "documents": PASSAGES},
        )
        found["rerank_scores"] = [
            round(r["relevance_score"], 4)
            for r in sorted(reply["results"], key=lambda r: -r["relevance_score"])
        ]
        reply, found["chat_again_s"] = timed(
            "/v1/chat/completions",
            {
                "model": "Qwen3.5-0.8B",
                "messages": [{"role": "user", "content": "Name one part of a car."}],
                "max_completion_tokens": 30,
            },
        )
        loaded = call("/v1/models")["data"]
        found["statuses"] = {m["id"]: m.get("status") for m in loaded}
        found["norm"] = round(math.sqrt(sum(x * x for x in vectors[0])), 6)
        try:
            call("/v1/chat/completions", {"messages": [{"role": "user", "content": "hi"}]})
            found["no_model"] = "accepted"
        except urllib.error.HTTPError as error:
            found["no_model"] = f"{error.code} {error.read()[:200]!r}"
    except Exception as error:
        found["error"] = f"{type(error).__name__}: {error}"[-3000:]
        found["log"] = (folder / "router.log").read_text(encoding="utf-8", errors="replace")[-3000:]
    finally:
        process.terminate()
        process.wait(timeout=60)
    print(json.dumps(found, indent=1, ensure_ascii=False), flush=True)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write(f"```json\n{json.dumps(found, indent=1, ensure_ascii=False)}\n```\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))

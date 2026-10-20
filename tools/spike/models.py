"""Spike: llama.cpp's server with embedding and reranking models on this machine, from the pinned
release build, before the Retrieval module's decision record.

Fetches the build for this system and four models, checks each against its size and sha256, and
for each model starts llama-server, times embedding or reranking passages of about 150 words,
checks that each test question finds its passage first, and prints what it found as JSON, and
into the job's summary on GitHub Actions.

    uv run --no-project --python 3.14 tools/spike/models.py <folder for downloads>
"""

import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

TAG = "b11734"
RELEASE = f"https://github.com/ggml-org/llama.cpp/releases/download/{TAG}"
BUILDS = {
    ("Windows", "AMD64"): (
        "bin-win-cpu-x64.zip",
        19667015,
        "bd6a8a8cb9d6ba115de3519d401f91dd5295b333243db44b6b8a3ce5e53ff8da",
    ),
    ("Darwin", "arm64"): (
        "bin-macos-arm64.tar.gz",
        12292927,
        "c823aad1d1c40728e8f1565663078fa2b3b7fd06bf484fa43e9e48b8b1b2509c",
    ),
    ("Linux", "x86_64"): (
        "bin-ubuntu-x64.tar.gz",
        17973484,
        "5d20cbcde04ef743b96e91b6173663b1925077a13fa86d0d98e69a5a5b59a16a",
    ),
    ("Linux", "aarch64"): (
        "bin-ubuntu-arm64.tar.gz",
        14023345,
        "29f2c5bb869e60ff25848d8f8b3b34dbe1b924c2266d4f54ee84c1106f148b23",
    ),
}
HF = "https://huggingface.co"
QWEN_TASK = "Given a web search query, retrieve relevant passages that answer the query"
MODELS = {
    "Qwen3-Embedding-0.6B": {
        "url": f"{HF}/Qwen/Qwen3-Embedding-0.6B-GGUF/resolve/"
        "370f27d7550e0def9b39c1f16d3fbaa13aa67728/Qwen3-Embedding-0.6B-Q8_0.gguf",
        "size": 639150592,
        "sha256": "06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439",
        "args": ["--embeddings", "--pooling", "last", "-c", "4096", "-b", "2048", "-ub", "2048"],
        "query": lambda q: f"Instruct: {QWEN_TASK}\nQuery:{q}",
        "document": lambda d: d,
    },
    "nomic-embed-text-v1.5": {
        "url": f"{HF}/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/"
        "0188c9bf409793f810680a5a431e7b899c46104c/nomic-embed-text-v1.5.Q8_0.gguf",
        "size": 146146432,
        "sha256": "3e24342164b3d94991ba9692fdc0dd08e3fd7362e0aacc396a9a5c54a544c3b7",
        "args": ["--embeddings", "--pooling", "mean", "-c", "2048", "-b", "2048", "-ub", "2048"],
        "query": lambda q: f"search_query: {q}",
        "document": lambda d: f"search_document: {d}",
    },
    "Qwen3-Reranker-0.6B": {
        "url": f"{HF}/ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF/resolve/"
        "a02f48bb4f057028298c21fa033da2b30d7742d5/qwen3-reranker-0.6b-q8_0.gguf",
        "size": 639153184,
        "sha256": "22c9979ce4fbcdc5acdc310c6641c32797eff1aa980b8f7a2db8a8ea23429a48",
        "args": ["--rerank", "-c", "4096", "-b", "2048", "-ub", "2048"],
    },
}
PORT = 8092
BASE = f"http://127.0.0.1:{PORT}"
PASSAGES = [
    "A flat tyre is usually a puncture in the inner tube. Take the wheel off, lever one side of "
    "the tyre off the rim, and pull the tube out. Pump a little air into it and listen or feel for "
    "the leak, then check the inside of the tyre for the thorn or glass that caused it, or the new "
    "tube will go flat too. Patch the hole or fit a new tube, put the tyre back on by hand, and "
    "pump it to the pressure printed on its side.",
    "A chain lasts longer when it is clean and oiled. Wipe it with a rag every few rides, and oil "
    "it every 150 kilometres or so, or after any ride in the rain. Put one drop of oil on each "
    "roller while turning the pedals backwards, let it soak in for a few minutes, then wipe off "
    "what is left on the outside, since oil on the outside only collects dirt.",
    "Brakes that squeal or feel weak usually need new pads or a cable adjustment. Pads wear down "
    "with use, and most have grooves that show when they are worn out. If the lever pulls almost "
    "to the handlebar before the brake bites, turn the barrel adjuster at the lever to take up "
    "the slack in the cable. Disc brakes that squeal may have oil on the rotor, which a clean rag "
    "and isopropyl alcohol will remove.",
    "Gears that skip or will not shift cleanly are often a matter of cable tension. Shift to the "
    "smallest rear sprocket, then turn the barrel adjuster on the derailleur half a turn at a "
    "time until each click moves the chain by exactly one sprocket. A bent derailleur hanger, "
    "often from a fall on the right side, also causes poor shifting and needs to be straightened "
    "with a special tool.",
    "To book a repair, choose a day and time on the booking page and say which bike it is and what "
    "is wrong with it. The workshop opens from 9 in the morning to 6 in the evening on weekdays and "
    "until 1 on Saturdays. Most repairs are done the same day, and the shop sends a message when "
    "the bike is ready to collect. A booking can be moved or cancelled up to two hours before.",
    "The right saddle height lets your leg almost straighten at the bottom of each pedal stroke, "
    "with a slight bend at the knee. Too low and your knees ache; too high and your hips rock from "
    "side to side. Raise or lower the seat post a centimetre at a time, and never past the minimum "
    "insertion mark stamped on it, or the frame may crack.",
    "A wheel that wobbles from side to side has a loose or broken spoke, or has been knocked out "
    "of true. Truing a wheel means tightening and loosening spokes a quarter turn at a time with a "
    "spoke key until the rim runs straight between the brake pads. A broken spoke should be "
    "replaced before riding far, since the wheel weakens quickly once one is gone.",
    "Before a long ride, check the tyre pressure, squeeze both brakes, spin each wheel to see that "
    "it runs straight, and look over the chain. Carry a spare tube, tyre levers, a small pump and "
    "a multi-tool. Lights are required after dark, and a bell is required in many places.",
]
QUESTIONS = [
    ("How do I fix a puncture?", 0),
    ("How often should I oil my chain?", 1),
    ("My brakes make a squealing noise", 2),
    ("When is the workshop open?", 4),
    ("How high should my seat be?", 5),
    ("What should I bring on a long ride?", 7),
]


def fetched(url, size, sha256, path):
    """The file at path, fetched from url unless it's already there, checked by size and sha256."""
    if not path.exists() or path.stat().st_size != size:
        started = time.time()
        urllib.request.urlretrieve(url, path)
        print(f"fetched {url} in {time.time() - started:.1f} s", flush=True)
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        while chunk := file.read(1 << 20):
            digest.update(chunk)
    assert path.stat().st_size == size, (path, path.stat().st_size)
    assert digest.hexdigest() == sha256, (path, digest.hexdigest())
    return path


def unpacked(archive, folder):
    """The llama-server executable from the build's archive, unpacked into folder."""
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as packed:
            packed.extractall(folder)
    else:
        with tarfile.open(archive) as packed:
            packed.extractall(folder, filter="tar")
    name = "llama-server.exe" if platform.system() == "Windows" else "llama-server"
    return next(folder.rglob(name))


def call(path, body=None, timeout=900):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def timed(path, body):
    started = time.time()
    reply = call(path, body)
    return reply, round(time.time() - started, 3)


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True)) / math.sqrt(
        sum(x * x for x in a) * sum(y * y for y in b)
    )


def embedding(name, model):
    found = {}
    documents = [model["document"](p) for p in PASSAGES]
    batch = [f"{documents[i % len(documents)]} ({i})" for i in range(64)]
    reply, found["64_passages_s"] = timed("/v1/embeddings", {"input": batch})
    found["usage"] = reply.get("usage")
    tokens = (reply.get("usage") or {}).get("prompt_tokens")
    if tokens:
        found["tokens_per_s"] = round(tokens / found["64_passages_s"], 1)
    found["dimensions"] = len(reply["data"][0]["embedding"])
    found["norm"] = round(math.sqrt(sum(x * x for x in reply["data"][0]["embedding"])), 6)
    reply, _ = timed("/v1/embeddings", {"input": documents})
    vectors = [item["embedding"] for item in sorted(reply["data"], key=lambda d: d["index"])]
    found["first_numbers"] = [round(x, 6) for x in vectors[0][:6]]
    rounded = json.dumps([[round(x, 4) for x in v] for v in vectors])
    found["rounded_sha256"] = hashlib.sha256(rounded.encode()).hexdigest()[:16]
    ranks = []
    seconds = []
    for question, answer in QUESTIONS:
        reply, spent = timed("/v1/embeddings", {"input": [model["query"](question)]})
        seconds.append(spent)
        query = reply["data"][0]["embedding"]
        order = sorted(range(len(vectors)), key=lambda i: -cosine(query, vectors[i]))
        ranks.append(order.index(answer) + 1)
    found["answer_ranks"] = ranks
    found["query_s"] = seconds
    try:
        tokens = call("/tokenize", {"content": "hello", "add_special": True})["tokens"]
        found["tokens_of_hello"] = tokens
    except OSError as error:
        found["tokenize"] = str(error)
    return found


def reranking(name, model):
    found = {}
    ranks = []
    seconds = []
    scores = []
    for question, answer in QUESTIONS:
        reply, spent = timed("/v1/rerank", {"query": question, "documents": PASSAGES})
        seconds.append(spent)
        order = [r["index"] for r in sorted(reply["results"], key=lambda r: -r["relevance_score"])]
        ranks.append(order.index(answer) + 1)
        scores.append([round(r["relevance_score"], 4) for r in reply["results"]][:3])
    found["answer_ranks"] = ranks
    found["8_passages_s"] = seconds
    found["first_scores"] = scores
    many = [f"{PASSAGES[i % len(PASSAGES)]} ({i})" for i in range(32)]
    reply, found["32_passages_s"] = timed("/v1/rerank", {"query": QUESTIONS[0][0], "documents": many})
    found["usage"] = reply.get("usage")
    return found


def serve(server, model_path, args, log_path):
    log = open(log_path, "w", encoding="utf-8")
    started = time.time()
    model = [] if model_path is None else ["-m", str(model_path)]
    process = subprocess.Popen(
        [str(server), *model, "--host", "127.0.0.1", "--port", str(PORT), *args],
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    while True:
        if process.poll() is not None:
            raise RuntimeError(log_path.read_text(encoding="utf-8", errors="replace")[-3000:])
        try:
            if call("/health", timeout=2).get("status") == "ok":
                break
        except OSError:
            pass
        time.sleep(0.5)
    return process, round(time.time() - started, 1)


def router(server, folder):
    """One llama-server in router mode, serving both Qwen3 models by name from a preset file."""
    found = {}
    preset = folder / "models.ini"
    embed = (folder / "Qwen3-Embedding-0.6B.gguf").resolve().as_posix()
    rerank = (folder / "Qwen3-Reranker-0.6B.gguf").resolve().as_posix()
    preset.write_text(
        "version = 1\n\n[*]\nc = 4096\nbatch-size = 2048\nubatch-size = 2048\n\n"
        f"[embeddings]\nmodel = {embed}\nembeddings = true\npooling = last\n\n"
        f"[reranker]\nmodel = {rerank}\nrerank = true\n",
        encoding="utf-8",
    )
    process, found["ready_s"] = serve(
        server, None, ["--models-preset", str(preset)], folder / "router.log"
    )
    try:
        found["models"] = [m["id"] for m in call("/v1/models")["data"]]
        reply, found["first_embedding_s"] = timed(
            "/v1/embeddings", {"model": "embeddings", "input": PASSAGES[:2]}
        )
        found["first_numbers"] = [round(x, 6) for x in reply["data"][0]["embedding"][:6]]
        reply, found["second_embedding_s"] = timed(
            "/v1/embeddings", {"model": "embeddings", "input": PASSAGES[:2]}
        )
        reply, found["first_rerank_s"] = timed(
            "/v1/rerank",
            {"model": "reranker", "query": QUESTIONS[0][0], "documents": PASSAGES},
        )
        found["rerank_top"] = max(reply["results"], key=lambda r: r["relevance_score"])["index"]
        try:
            call("/v1/embeddings", {"model": "missing", "input": ["x"]})
            found["unknown_model"] = "accepted"
        except urllib.error.HTTPError as error:
            found["unknown_model"] = f"{error.code} {error.read()[:200]!r}"
    finally:
        process.terminate()
        process.wait(timeout=60)
    return found


def main(folder):
    folder.mkdir(parents=True, exist_ok=True)
    found = {
        "system": f"{platform.system()} {platform.release()} {platform.machine()}",
        "processor": platform.processor(),
        "cpus": os.cpu_count(),
    }
    build, size, sha256 = BUILDS[(platform.system(), platform.machine())]
    archive = fetched(f"{RELEASE}/llama-{TAG}-{build}", size, sha256, folder / f"llama-{build}")
    server = unpacked(archive, folder / "llama")
    # On a Mac the server runs a model on the GPU, through Metal, and with --device none on the
    # CPU alone, as it does on the other systems.
    runs = [(name, model, []) for name, model in MODELS.items()]
    if platform.system() == "Darwin":
        runs += [
            (f"{name} on the CPU", model, ["--device", "none"])
            for name, model in MODELS.items()
            if name.startswith("Qwen3")
        ]
    for label, model, extra in runs:
        name = label.removesuffix(" on the CPU")
        result = {}
        try:
            path = fetched(model["url"], model["size"], model["sha256"], folder / f"{name}.gguf")
            process, result["ready_s"] = serve(
                server, path, model["args"] + extra, folder / f"{label}.log"
            )
            try:
                result |= (embedding if "query" in model else reranking)(name, model)
            finally:
                process.terminate()
                process.wait(timeout=60)
        except Exception as error:
            result["error"] = f"{type(error).__name__}: {error}"[-3000:]
        found[label] = result
        print(json.dumps({label: result}, indent=1), flush=True)
    try:
        found["router"] = router(server, folder)
    except Exception as error:
        found["router"] = {"error": f"{type(error).__name__}: {error}"[-3000:]}
    print(json.dumps({"router": found["router"]}, indent=1), flush=True)
    report = json.dumps(found, indent=1, ensure_ascii=False)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write(f"```json\n{report}\n```\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))

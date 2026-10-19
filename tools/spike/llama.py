"""Spike: llama.cpp's server with Qwen3.5-0.8B on this machine, from the pinned release build.

Fetches the build for this system and the model, checks each against its size and sha256, starts
llama-server, asks it for a greedy reply, a reply held to a JSON schema, a tool call and a streamed
reply, and prints what it found as JSON, and into the job's summary on GitHub Actions.

    uv run --no-project --python 3.14 tools/spike/llama.py <folder for downloads>
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
import tarfile
import time
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
    ("Windows", "ARM64"): (
        "bin-win-cpu-arm64.zip",
        12549827,
        "7f4c5a8a9d0129c4b541c4b057da2e8052f9f6819e105d00f5b26e8bf86205a2",
    ),
    ("Darwin", "arm64"): (
        "bin-macos-arm64.tar.gz",
        12292927,
        "c823aad1d1c40728e8f1565663078fa2b3b7fd06bf484fa43e9e48b8b1b2509c",
    ),
    ("Darwin", "x86_64"): (
        "bin-macos-x64.tar.gz",
        11781759,
        "696521c81f21816e5b7686aa308425004ee1ec1fc2d2679414e9e6fa0aa8fbfc",
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
MODEL = (
    "https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF/resolve/"
    "8fea620810c4afa23dd6443f999a48574c1611a3/Qwen3.5-0.8B-Q8_0.gguf",
    833592096,
    "37ae482d336108d23516fa35e8e0c4126688d81018b87178a18d752a1357814f",
)
PORT = 8091
BASE = f"http://127.0.0.1:{PORT}"
NO_THINKING = {"enable_thinking": False}
STORY = [
    {
        "role": "user",
        "content": "Write three short sentences about a cat who likes rain.",
    }
]
ORDER = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"type": "integer", "minimum": 1},
                },
                "required": ["name", "quantity"],
                "additionalProperties": False,
            },
        },
        "address": {"type": "string"},
    },
    "required": ["items", "address"],
    "additionalProperties": False,
}
WEATHER = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}


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


def call(path, body=None, timeout=600):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def chat(**body):
    started = time.time()
    reply = call("/v1/chat/completions", {"chat_template_kwargs": NO_THINKING, **body})
    return reply, time.time() - started


def streamed(**body):
    """The text of a streamed reply and how many chunks it came in."""
    request = urllib.request.Request(
        BASE + "/v1/chat/completions",
        data=json.dumps(
            {"chat_template_kwargs": NO_THINKING, "stream": True, **body}
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    text, chunks = [], 0
    with urllib.request.urlopen(request, timeout=600) as response:
        for line in response:
            line = line.decode().strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            chunks += 1
            for choice in json.loads(line[6:]).get("choices", []):
                text.append(choice["delta"].get("content") or "")
    return "".join(text), chunks


def windows_facts(server):
    """Whether the server is signed, and whether the C++ runtime it loads is installed."""
    script = f"(Get-AuthenticodeSignature '{server}').Status"
    status = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True
    ).stdout.strip()
    system = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    runtime = {
        name: (system / name).exists()
        for name in ["msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"]
    }
    return {"signature": status, "runtime_in_system32": runtime}


def main(folder):
    folder.mkdir(parents=True, exist_ok=True)
    found = {
        "system": platform.system(),
        "machine": platform.machine(),
        "release": platform.release(),
        "processor": platform.processor(),
        "cpus": os.cpu_count(),
    }
    build, size, sha256 = BUILDS[(platform.system(), platform.machine())]
    archive = fetched(
        f"{RELEASE}/llama-{TAG}-{build}", size, sha256, folder / f"llama-{build}"
    )
    server = unpacked(archive, folder / "llama")
    found["build"] = build
    if platform.system() == "Windows":
        found |= windows_facts(server)
    model = fetched(*MODEL, folder / "Qwen3.5-0.8B-Q8_0.gguf")
    log = open(folder / "server.log", "w")
    started = time.time()
    process = subprocess.Popen(
        [str(server), "-m", str(model), "--host", "127.0.0.1", "--port", str(PORT)]
        + ["-c", "4096"],
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        while True:
            assert process.poll() is None, (folder / "server.log").read_text()[-4000:]
            try:
                if call("/health", timeout=2).get("status") == "ok":
                    break
            except OSError:
                pass
            time.sleep(0.5)
        found["ready_seconds"] = round(time.time() - started, 1)
        replies = []
        for _ in range(2):
            reply, seconds = chat(messages=STORY, temperature=0, max_tokens=64)
            replies.append(reply["choices"][0]["message"]["content"])
        timings = reply.get("timings", {})
        found["greedy"] = {
            "text": replies[0],
            "same_twice": replies[0] == replies[1],
            "seconds": round(seconds, 2),
            "prompt_per_second": round(timings.get("prompt_per_second", 0), 1),
            "predicted_per_second": round(timings.get("predicted_per_second", 0), 1),
        }
        for key, message in [
            (
                "schema",
                "Hi, I want 2 large pepperoni pizzas and one garlic bread delivered to 14 Elm Street.",
            ),
            (
                "schema_short",
                "Two large pepperoni pizzas and a garlic bread to 14 Elm Street.",
            ),
        ]:
            reply, seconds = chat(
                messages=[
                    {
                        "role": "system",
                        "content": "Extract the order from the message.",
                    },
                    {"role": "user", "content": message},
                ],
                temperature=0,
                max_tokens=200,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "order", "schema": ORDER},
                },
            )
            content = reply["choices"][0]["message"]["content"]
            try:
                parsed = sorted(json.loads(content))
            except json.JSONDecodeError as error:
                parsed = str(error)
            found[key] = {
                "text": content[:300],
                "finish_reason": reply["choices"][0]["finish_reason"],
                "completion_tokens": reply["usage"]["completion_tokens"],
                "parsed": parsed,
                "seconds": round(seconds, 2),
            }
        reply, seconds = chat(
            messages=[{"role": "user", "content": "What is the weather in Toronto?"}],
            temperature=0,
            max_tokens=200,
            tools=[WEATHER],
        )
        message = reply["choices"][0]["message"]
        found["tool"] = {
            "finish_reason": reply["choices"][0]["finish_reason"],
            "calls": [call["function"] for call in message.get("tool_calls") or []],
            "seconds": round(seconds, 2),
        }
        text, chunks = streamed(messages=STORY, temperature=0, max_tokens=64)
        found["stream"] = {"chunks": chunks, "same_as_greedy": text == replies[0]}
    finally:
        process.terminate()
        process.wait(timeout=60)
    report = json.dumps(found, indent=1, ensure_ascii=False)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write(f"```json\n{report}\n```\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))

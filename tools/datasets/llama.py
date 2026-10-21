"""What the data tools that record a model's answers share: the model's weights, downloaded and
checked, and llama.cpp's llama-server, release b11734, running it at a free port."""

import hashlib
import json
import socket
import subprocess
import time
import urllib.request
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

LLAMA = "11734"


def download(url: str, sha256: str, path: Path) -> Path:
    """The file at url, downloaded to path unless it is already there, and checked."""
    if not path.exists():
        partial = path.with_name(path.name + ".partial")
        with urllib.request.urlopen(url) as response, open(partial, "wb") as file:
            while chunk := response.read(1 << 20):
                file.write(chunk)
        partial.replace(path)
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        while chunk := file.read(1 << 20):
            digest.update(chunk)
    if digest.hexdigest() != sha256:
        raise SystemExit(f"{path.name} has changed: sha256 {digest.hexdigest()}.")
    return path


@contextmanager
def serving(
    program: Path, model: Path, options: list[str], log: Path
) -> Iterator[Callable[[str, dict], dict]]:
    """A function that posts a body to one of the server's paths and gives its reply, with the
    model running in llama-server with the options given, for as long as the block runs."""
    version = subprocess.run([program, "--version"], capture_output=True, text=True, check=False)
    if f"(build {LLAMA}," not in version.stdout + version.stderr:
        raise SystemExit(f"{program} is not llama.cpp's release b{LLAMA}.")
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
    address = f"http://127.0.0.1:{port}"

    def post(path: str, body: dict) -> dict:
        request = urllib.request.Request(
            f"{address}{path}",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    post.address = address  # type: ignore[attr-defined]

    with open(log, "wb") as output:
        command = [program, "--model", model, *options, "--port", str(port)]
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 300
            while True:
                try:
                    with urllib.request.urlopen(f"{address}/health") as response:
                        if response.status == 200:
                            break
                except OSError:
                    if time.monotonic() > deadline:
                        raise SystemExit("llama-server didn't start.") from None
                    time.sleep(0.5)
            yield post
        finally:
            process.terminate()
            process.wait()


def address(post: Callable[[str, dict], dict]) -> str:
    """The address of the server a function from serving posts to, such as
    http://127.0.0.1:50123."""
    return post.address  # type: ignore[attr-defined]

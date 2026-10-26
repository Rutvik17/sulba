"""Runs a lab's stages on your machine, with the tests and checks its page runs in the browser.

    uv run sulba.py          run the tests of the stage you're on
    uv run sulba.py finish   finish a Catch stage's review
    uv run sulba.py next     start the next stage, once this one is done
    uv run sulba.py model    start the lab's models, for your code to call
    uv run sulba.py db       start the lab's database, for your code to use
    uv run sulba.py build    build the lab's TypeScript into JavaScript for the browser

When a stage is done, it gives you a link to the lab's page, which marks the stage done there.
Before the first run, it fetches into data/ any files the lab needs that are too large for the
download, such as a dataset, from their publishers.

A lab with models serves them with llama.cpp's server until you press Ctrl+C, each by its name.
The first time, it fetches them and the server into sulba in your cache folder, where every lab
finds them.

A lab with a database runs Postgres, with pgvector, until you press Ctrl+C. It keeps what you
put in it in .sulba/database, and answers only programs on this computer. On Linux, the first
time, it fetches pgvector into sulba in your cache folder.

A lab with TypeScript stages runs their tests in Node.js. The first time, it fetches Node.js and
the lab's packages into sulba in your cache folder. Its build compiles the TypeScript its
tsconfig.build.json names, with the lab's own TypeScript, for a browser to load.

A lab with Go stages runs their tests with Go. The first time, it fetches Go into sulba in your
cache folder.
"""

# A lab that runs on the learner's machine downloads with this file at its top and its stages in
# .sulba/lab.json (decision record 28). The link's fragment carries the stage's attempts as the
# attempts table takes them (decision record 18), so the page records them as its own; a fragment
# never reaches the server. It holds them as JSON compressed with DEFLATE, in base64url. The files
# a lab fetches are each pinned by its size and sha256 (decision record 29), as are a lab's models
# and the build of llama.cpp's server that serves them (decision record 34).

from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import http.client
import http.server
import json
import os
import platform
import secrets
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
import webbrowser
import zipfile
import zlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
RUNNER = HERE / ".sulba"
# The runner's modules sit in .sulba in a download, and beside this file in the repository.
sys.path.insert(0, str(RUNNER))

# The longest an attempt counts, as the attempts table allows.
MAX_SECONDS = 3600
# The most attempts a link carries: a stage's runs since the last link, and its pass.
MAX_ATTEMPTS = 200
# The longest link the runner makes. Parts of Windows still cut an address at 2,083 characters, so
# a link holds the newest of its attempts that fit in this.
MAX_LINK = 2000
# A fetch writes its file in parts of this many bytes.
CHUNK = 1 << 20
# How long a fetch waits on its publisher to connect or send more, in seconds.
TIMEOUT = 60
# How many times a run asks a publisher for a file, each time for the rest of it, before it leaves
# what came for the next run to go on from.
TRIES = 5
# The release of llama.cpp whose server serves a lab's models, where its releases are, and its CPU
# build for each system, by the names Python gives the system and the machine: the build's archive,
# its size and its sha256.
LLAMA = "b11734"
LLAMA_RELEASES = "https://github.com/ggml-org/llama.cpp/releases/download"
LLAMA_BUILDS = {
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
# Where the models answer, at llama.cpp's own port.
PORT = 9931
# The project's files a lab's TypeScript runs with, beside the learner's: the packages Node runs
# the tests with, and tsc's settings (decision record 39).
NODE_FILES = ["package.json", "package-lock.json", "tsconfig.json"]
# The project's file a lab's Go runs with: the module its tests import the learner's package from
# (decision record 43).
GO_FILES = ["go.mod"]
# The headers about one connection, not the request or the answer they come with, which the
# forwarder sets for each of its connections itself.
HOP_BY_HOP = {
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-connection",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}
# How the server runs each kind of model, in its preset file's options: a chat model reads a
# conversation of up to 4,096 tokens, or the context its lab gives it (decision record 36), with
# reasoning off, an embedding model embeds a text of up to 2,048 tokens in one pass, and a reranker
# scores a query and a document of up to 2,048 tokens together, in a context of 4,096 (decision
# record 34).
KINDS = {
    "chat": {"ctx-size": "4096", "reasoning": "off"},
    "embedding": {
        "embeddings": "true",
        "ctx-size": "2048",
        "batch-size": "2048",
        "ubatch-size": "2048",
    },
    "reranking": {
        "reranking": "true",
        "ctx-size": "4096",
        "batch-size": "2048",
        "ubatch-size": "2048",
    },
}
# The Visual C++ runtime's DLLs llama.cpp's Windows builds need, by machine, and the address of
# Microsoft's installer of them.
VC_RUNTIME = {
    "AMD64": (
        ["msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"],
        "https://aka.ms/vc14/vc_redist.x64.exe",
    ),
    "ARM64": (["msvcp140.dll", "vcruntime140.dll"], "https://aka.ms/vc14/vc_redist.arm64.exe"),
}
# How long the server may take to start and load the lab's models, or to answer the check's request
# to one, before the runner gives up, in seconds.
LOADING = 600
# Where the lab's database answers, at Postgres's own port.
DATABASE_PORT = 5432


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="uv run sulba.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["run", "finish", "next", "model", "db", "build"],
        default="run",
    )
    parser.add_argument(
        "--port",
        type=int,
        help=f"the port the models or database answer at ({PORT} and {DATABASE_PORT} by default)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="ask each model one question, show its answer and stop (model only)",
    )
    args = parser.parse_args(argv)
    command = args.command
    if not (RUNNER / "lab.json").is_file():
        print("Run this in the folder of a lab you downloaded: it has no .sulba/lab.json.")
        return 1
    lab = json.loads((RUNNER / "lab.json").read_text(encoding="utf-8"))
    if command == "model":
        return serve_model(lab, args.port or PORT, check=args.check)
    if command == "db":
        return serve_database(args.port or DATABASE_PORT)
    if command == "build":
        return build()
    progress = load_progress(lab)
    if command == "next":
        code = start_next(lab, progress)
    else:
        code = run_stage(lab, progress, finishing=command == "finish")
    (RUNNER / "progress.json").write_text(json.dumps(progress, indent=2), encoding="utf-8")
    return code


def build() -> int:
    """Compiles the lab's TypeScript into JavaScript for the browser, as its tsconfig.build.json
    says, with the TypeScript its package-lock.json pins, fetched the first time as for a run."""
    if not (HERE / "tsconfig.build.json").is_file():
        print("This lab has no TypeScript to build for the browser.")
        return 1
    import sulba_fixtures
    import sulba_runner

    files = {name: (HERE / name).read_text(encoding="utf-8") for name in NODE_FILES}
    if sulba_runner.fetches_first(files):
        print(f"Fetching Node.js {sulba_runner.NODE} and the lab's packages for TypeScript into")
        print(f"{sulba_fixtures.cache_folder()}, the first time.\n")
    try:
        node, npm = sulba_runner.node_program()
        packages = sulba_runner.node_packages(node, npm, files)
    except RuntimeError as error:
        print(error)
        return 1
    tsc = packages / "node_modules" / "typescript" / "bin" / "tsc"
    # tsc writes its errors to the terminal itself, after what this has printed.
    sys.stdout.flush()
    built = subprocess.run([node, tsc, "-p", "tsconfig.build.json"], cwd=HERE, check=False)
    if built.returncode != 0:
        print("\nFix the errors, then build again.")
        return 1
    print("Built the lab's TypeScript for the browser.")
    return 0


def load_progress(lab: dict[str, Any]) -> dict[str, Any]:
    """Where the learner is: the stage they're on, the stages they've done with each Catch
    review, the attempts no link has carried yet, and when they last ran a stage's tests."""
    path = RUNNER / "progress.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"stage": lab["start"], "passed": {}, "attempts": [], "last": None}


def run_stage(lab: dict[str, Any], progress: dict[str, Any], *, finishing: bool) -> int:
    stages = lab["stages"]
    index = progress["stage"]
    stage = stages[index]
    print(f"Stage {index + 1} of {len(stages)}: {stage['title']}\n")
    if finishing and stage["kind"] != "catch":
        print("Only a Catch stage has a review to finish.")
        return 1
    if finishing and stage["id"] in progress["passed"]:
        print("This review is finished.")
        return 0
    if not fetched(lab):
        return 1
    import sulba_fixtures
    import sulba_runner

    files = session_files(lab, index)
    if any(name.endswith(".ts") for name in stage["tests"]) and sulba_runner.fetches_first(files):
        print(f"Fetching Node.js {sulba_runner.NODE} and the lab's packages for TypeScript into")
        print(f"{sulba_fixtures.cache_folder()}, the first time.\n")
    if any(name.endswith(".go") for name in stage["tests"]) and sulba_runner.go_fetches_first():
        print(
            f"Fetching Go {sulba_runner.GO} into {sulba_fixtures.cache_folder()}, the first time.\n"
        )
    result = json.loads(
        sulba_runner.run(
            json.dumps(files), json.dumps(list(stage["tests"])), json.dumps(session_links(lab))
        )
    )
    report(stage, result)
    tests, checks = split(stage, result)
    progress["attempts"].append(attempt(progress, stage, "run", tests, checks, None))
    caught = [test["id"] for test in checks if test["status"] == "pass"]
    done = status_of(result) == "pass"
    if stage["id"] in progress["passed"]:
        if done:
            print("\nThis stage is done.", following(lab, index))
        return 0 if done else 1
    if stage["kind"] == "catch":
        # A review finishes by itself once the code passes every test and check.
        if not (finishing or done):
            return 1
        if result["problem"] or not result["tests"]:
            print("\nFix the error, then finish the review.")
            return 1
        review = {"caught": caught, "problems": len(stage["checks"])}
        passed(progress, stage, review)
        print(f"\nReview finished. You caught {len(caught)} of {len(stage['checks'])} problems.")
    elif done:
        passed(progress, stage, None)
        print(f"\nStage {index + 1} done.")
    else:
        return 1
    show_link(link(lab, progress))
    progress["attempts"] = []
    print(following(lab, index))
    return 0


def session_files(lab: dict[str, Any], index: int) -> dict[str, str]:
    """A run's files: the lab's datasets and references, the files it gives, the project's files
    for TypeScript and Go, the learner's files up to this stage, and the stage's tests and
    checks. Of data/, only the lab's own datasets are read: it also holds the files the lab
    fetches, and whatever the learner puts there."""
    files: dict[str, str] = {}
    for name in [*lab["data"], *lab["given"], *NODE_FILES, *GO_FILES]:
        if (HERE / name).is_file():
            files[name] = (HERE / name).read_text(encoding="utf-8")
    folder = RUNNER / "references"
    for path in sorted(folder.rglob("*")) if folder.is_dir() else []:
        if path.is_file():
            name = f"references/{path.relative_to(folder).as_posix()}"
            files[name] = path.read_text(encoding="utf-8")
    for stage in lab["stages"][: index + 1]:
        path = HERE / stage["file"]
        if path.is_file():
            files[stage["file"]] = path.read_text(encoding="utf-8")
    for name, text in lab["stages"][index]["tests"].items():
        files[name] = decoded(text)
    return files


def session_links(lab: dict[str, Any]) -> dict[str, str]:
    """The files the lab fetches, by their path in a run, each where it is in data/."""
    return {f"data/{each['file']}": str(HERE / "data" / each["file"]) for each in lab["fetch"]}


def decoded(text: str) -> str:
    return base64.b64decode(text).decode("utf-8")


class Mismatch(Exception):
    """A publisher sent a file other than the one its sha256 names."""


def fetched(lab: dict[str, Any]) -> bool:
    """Puts in data/ each file the lab fetches from its publisher, fetching those not there yet,
    and says why when one can't be fetched. Returns whether they are all there."""
    files = [(each, HERE / "data" / each["file"], each["file"]) for each in lab["fetch"]]
    return fetched_each("Fetching the lab's files into data:", files)


def fetched_each(heading: str, files: list[tuple[dict[str, Any], Path, str]]) -> bool:
    """Puts each file at its path, fetching those not there yet under heading, each by its name,
    and says why when one can't be fetched. Returns whether they are all there."""
    missing = [(file, path, name) for file, path, name in files if not whole(path, file)]
    if not missing:
        return True
    print(heading)
    for each, path, name in missing:
        host = urlsplit(each["url"]).hostname
        about = f"  {name}, {size(each['bytes'])}, from {host}"
        print(about, end="", flush=True)
        try:
            fetch(each, path, about)
        except urllib.error.HTTPError as error:
            print(f"\n\n{host} answered {error.code} {error.reason}. Try again later.")
            return False
        except Mismatch:
            print(f"\n\n{host} sent a different file from the one the lab was made with.")
            print("Try again later.")
            return False
        except (OSError, http.client.HTTPException) as error:
            print(f"\n\nThe fetch stopped: {error}")
            print("Run uv run sulba.py again to go on from where it stopped.")
            return False
        print()
    print()
    return True


def fetch(file: dict[str, Any], path: Path, about: str) -> None:
    """Fetches the file to path, through a file beside it that a fetch cut short goes on from, and
    moves it into place once it's whole."""
    partial = path.with_name(f"{path.name}.partial")
    path.parent.mkdir(parents=True, exist_ok=True)
    # A fetch stopped after all of its file had come has only to move it into place.
    if not whole(partial, file):
        kept = partial.is_file()
        receive_all(file, partial, about)
        if kept and not whole(partial, file):
            # What a fetch cut short kept may not be the start of this file, so it starts again.
            partial.unlink()
            receive_all(file, partial, about)
        if not whole(partial, file):
            partial.unlink()
            raise Mismatch(file["url"])
    os.replace(partial, path)


def receive_all(file: dict[str, Any], partial: Path, about: str) -> None:
    """Receives the file into partial, asking again for the rest when the publisher stops sending
    or can't be reached, up to TRIES times in all. An answer with an error is final."""
    for tried in range(1, TRIES + 1):
        try:
            receive(file, partial, about)
            return
        except (OSError, http.client.HTTPException) as error:
            if isinstance(error, urllib.error.HTTPError) or tried == TRIES:
                raise


def receive(file: dict[str, Any], partial: Path, about: str) -> None:
    """Writes the file into partial: the part after what partial holds, or all of it when partial
    holds no less than the whole file or the publisher sends all of it. At a terminal, it shows how
    much has come after `about`. A publisher whose answer is another size of file has another file,
    and one that stops early leaves partial for the next fetch to go on from."""
    start = partial.stat().st_size if partial.is_file() else 0
    if start >= file["bytes"]:
        start = 0
    headers = {"User-Agent": "sulba.py"}
    if start:
        headers["Range"] = f"bytes={start}-"
    request = urllib.request.Request(file["url"], headers=headers)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        if response.status != 206:
            start = 0
        if declared(response, start) not in (None, file["bytes"]):
            partial.unlink(missing_ok=True)
            raise Mismatch(file["url"])
        with partial.open("ab" if start else "wb") as out:
            done = start
            while chunk := response.read(CHUNK):
                out.write(chunk)
                done += len(chunk)
                if sys.stdout.isatty():
                    shown = min(100, done * 100 // file["bytes"])
                    print(f"\r{about}: {shown}%", end="", flush=True)
        # http.client ends a read early without an error when the connection closes.
        if done < file["bytes"]:
            host = urlsplit(file["url"]).hostname
            raise ConnectionError(f"{host} stopped after {size(done)} of {size(file['bytes'])}")


def serve_model(lab: dict[str, Any], port: int, *, check: bool) -> int:
    """Starts the lab's models in llama.cpp's server, fetching them and the server into the cache
    folder the first time, and keeps them answering, each by its name, until Ctrl+C. With check, it
    asks each model one thing instead, shows its answer and stops."""
    models = lab.get("models", [])
    if not models:
        print("This lab has no model to run.")
        return 1
    system, machine = platform.system(), platform.machine()
    build = LLAMA_BUILDS.get((system, machine))
    if build is None:
        print(f"llama.cpp has no build of its server for {system} on {machine}.")
        return 1
    if system == "Windows":
        names, installer = VC_RUNTIME[machine]
        system32 = Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "System32"
        if not all((system32 / each).exists() for each in names):
            print("llama.cpp's server needs Microsoft's Visual C++ runtime, which this computer")
            print(f"doesn't have yet. Install it from {installer}, then run this again.")
            return 1
    import sulba_fixtures

    name, bytes_, sha256 = build
    url = f"{LLAMA_RELEASES}/{LLAMA}/llama-{LLAMA}-{name}"
    archive = {"url": url, "bytes": bytes_, "sha256": sha256}
    folder = sulba_fixtures.cache_folder()
    archive_path = folder / "llama.cpp" / LLAMA / name
    # Each model's weights, from the cache folder, where the server runs.
    weights = [
        Path("models", model["sha256"], urlsplit(model["url"]).path.split("/")[-1])
        for model in models
    ]
    files = [(archive, archive_path, f"llama.cpp's server {LLAMA}")]
    files += [
        (model, folder / path, model["title"]) for model, path in zip(models, weights, strict=True)
    ]
    which = "model and its server" if len(models) == 1 else "models and their server"
    if not fetched_each(f"Fetching the {which} into {folder}:", files):
        return 1
    server = unpacked(archive_path)
    preset = f"models-{port}.ini"
    (folder / preset).write_text(preset_of(models, weights, system), encoding="utf-8")
    command = [str(server), "--models-preset", preset, "--models-max", str(len(models))]
    command += ["--host", "127.0.0.1"]
    return serve(command, folder, models, port, check=check)


def preset_of(models: list[dict[str, Any]], weights: list[Path], system: str) -> str:
    """The server's preset file: a section for each model, named by its title, with its weights,
    loaded as the server starts, and the options of its kind, with a chat model's context where
    its lab gives one (decision record 36). On macOS a chat model runs on the GPU, through Metal,
    and the others on the CPU (decision record 34)."""
    lines = ["version = 1"]
    for model, path in zip(models, weights, strict=True):
        options = {"model": path.as_posix(), "load-on-startup": "true", **KINDS[model["kind"]]}
        if "context" in model:
            options["ctx-size"] = str(model["context"])
        if system == "Darwin" and model["kind"] != "chat":
            options["device"] = "none"
        lines += [
            "",
            f"[{model['title']}]",
            *(f"{key} = {value}" for key, value in options.items()),
        ]
    return "\n".join(lines) + "\n"


def serve_database(port: int) -> int:
    """Starts the lab's database, a Postgres server with pgvector that keeps its data in
    .sulba/database, and keeps it running until Ctrl+C (decision record 33)."""
    import sulba_fixtures

    try:
        binaries = sulba_fixtures.postgres_binaries()
    except RuntimeError as error:
        print(f"This lab has no database: {error}")
        return 1
    data = RUNNER / "database"
    secret = RUNNER / "database-password"
    pg_ctl = binaries / sulba_fixtures.executable("pg_ctl")
    if not (data / "PG_VERSION").is_file():
        shutil.rmtree(data, ignore_errors=True)
        # Readable by the learner alone, where the system allows it.
        handle = os.open(secret, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(secrets.token_urlsafe(16))
    elif sulba_fixtures.run_postgres([pg_ctl, "status", "-D", data], check=False) == 0:
        # Left running by a runner that was stopped some other way than Ctrl+C.
        sulba_fixtures.run_postgres([pg_ctl, "stop", "-D", data, "-m", "fast", "-w"], check=False)
    if in_use(port):
        print(
            f"Port {port} is in use, perhaps by another database. Stop that, or run "
            f"uv run sulba.py db --port {port + 1}."
        )
        return 1
    password = secret.read_text(encoding="utf-8")
    url = f"postgresql://postgres:{password}@127.0.0.1:{port}/postgres"
    try:
        sulba_fixtures.start_postgres(binaries, data, port, password)
        sulba_fixtures.run_postgres(
            [
                binaries / sulba_fixtures.executable("psql"),
                "--no-psqlrc",
                "-c",
                "CREATE EXTENSION IF NOT EXISTS vector",
                url,
            ]
        )
    except RuntimeError as error:
        print(f"The database couldn't start: {error}")
        return 1
    print(f"The database answers at {url}. Press Ctrl+C to stop it.", flush=True)
    # Ctrl+C stops it however the runner was started, and so does the terminal closing.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    for name in ("SIGTERM", "SIGHUP", "SIGBREAK"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), signal.default_int_handler)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        sulba_fixtures.run_postgres([pg_ctl, "stop", "-D", data, "-m", "fast", "-w"], check=False)
    print("Stopped the database.")
    return 0


def unpacked(archive: Path) -> Path:
    """The server's program from the build's archive, unpacked beside it the first time."""
    program = "llama-server.exe" if archive.name.endswith(".zip") else "llama-server"
    folder = archive.parent / "server"
    found = next(folder.rglob(program), None) if folder.is_dir() else None
    if found is not None:
        return found
    shutil.rmtree(folder, ignore_errors=True)
    # Unpacked beside the archive first, so a run stopped halfway leaves no server to find.
    unpacking = Path(tempfile.mkdtemp(dir=archive.parent))
    try:
        if archive.name.endswith(".zip"):
            with zipfile.ZipFile(archive) as packed:
                packed.extractall(unpacking)
        else:
            with tarfile.open(archive) as packed:
                packed.extractall(unpacking, filter="data")
        os.replace(unpacking, folder)
    finally:
        shutil.rmtree(unpacking, ignore_errors=True)
    return next(folder.rglob(program))


def serve(
    command: list[str], folder: Path, models: list[dict[str, Any]], port: int, *, check: bool
) -> int:
    """Runs the server in folder, behind a forwarder at the port, with its output in a log there,
    says where the models answer once it has loaded them all, and keeps it running until Ctrl+C.
    With check, it asks each model one thing instead and stops."""
    if in_use(port):
        print(port_in_use(port))
        return 1
    try:
        forwarder = Forwarder(port)
    except OSError:
        # Something holds the port without answering at it.
        print(port_in_use(port))
        return 1
    with forwarder:
        threading.Thread(target=forwarder.serve_forever, daemon=True).start()
        try:
            command = [*command, "--port", str(forwarder.target)]
            return run_server(command, folder, models, port, check=check)
        finally:
            forwarder.shutdown()


def run_server(
    command: list[str], folder: Path, models: list[dict[str, Any]], port: int, *, check: bool
) -> int:
    """Runs the server as serve says, once the forwarder holds the port."""
    address = f"http://127.0.0.1:{port}"
    titles = listed([model["title"] for model in models])
    log = folder / f"server-{port}.log"
    with log.open("wb") as output:
        try:
            process = subprocess.Popen(command, cwd=folder, stdout=output, stderr=subprocess.STDOUT)
        except OSError as error:
            print(f"llama.cpp's server couldn't start: {error}")
            return 1
        try:
            print(f"Loading {titles}...", flush=True)
            unloaded = loading(process, address, models)
            if unloaded:
                print(stopped(log) if process.poll() is not None else failed(log, unloaded))
                return 1
            if check:
                return asked(address, models)
            if len(models) == 1:
                print(f"{titles} answers at {address}/v1, by that name.", end=" ")
                print("Press Ctrl+C to stop it.", flush=True)
            else:
                print(f"{titles} answer at {address}/v1, each by its name.", end=" ")
                print("Press Ctrl+C to stop them.", flush=True)
            try:
                process.wait()
            except KeyboardInterrupt:
                print(f"Stopped {titles}.")
                return 0
            print(stopped(log))
            return 1
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()


class Forwarder(socketserver.ThreadingTCPServer):
    """Where a lab's models answer: it passes each request to llama.cpp's server, at a port of its
    own on this computer, and the server's answer back as it comes. In router mode, the server
    closes a connection after each answer without saying so, and a program that sends its next
    request on the connection before it closes gets no answer. The forwarder keeps each program's
    connection open instead (decision record 35)."""

    daemon_threads = True
    # Lets the runner start again at once at a port it has just left. On Windows the option would
    # let it share a port another program holds.
    allow_reuse_address = os.name != "nt"

    def __init__(self, port: int) -> None:
        super().__init__(("127.0.0.1", port), Forwarded)
        # Where the server answers, behind the forwarder.
        self.target = free_port()


class Forwarded(http.server.BaseHTTPRequestHandler):
    """A program's connection to the forwarder, open from one request to the next."""

    protocol_version = "HTTP/1.1"
    server: Forwarder

    def do_GET(self) -> None:
        self.forward()

    def do_POST(self) -> None:
        self.forward()

    def forward(self) -> None:
        """Sends the request on to the server, on a connection of its own, and its answer back in
        chunks as they come, so that a streamed reply streams."""
        body = self.body()
        headers = {
            key: value for key, value in self.headers.items() if key.lower() not in HOP_BY_HOP
        }
        with contextlib.closing(http.client.HTTPConnection("127.0.0.1", self.server.target)) as to:
            try:
                to.request(self.command, self.path, body, {**headers, "Connection": "close"})
                answer = to.getresponse()
            except OSError:
                # Nothing answers at the server's port until it has started.
                self.starting()
                return
            self.send_response_only(answer.status, answer.reason)
            for key, value in answer.getheaders():
                if key.lower() not in HOP_BY_HOP:
                    self.send_header(key, value)
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            try:
                while chunk := answer.read1():
                    self.wfile.write(b"%X\r\n%s\r\n" % (len(chunk), chunk))
                self.wfile.write(b"0\r\n\r\n")
            except OSError, http.client.HTTPException:
                # The program or the server closed its connection before the answer ended, which
                # the program learns as this connection closes too.
                self.close_connection = True

    def body(self) -> bytes:
        """The request's body, whether it gives its length or comes in chunks."""
        if "chunked" not in self.headers.get("Transfer-Encoding", "").lower():
            return self.rfile.read(int(self.headers.get("Content-Length") or 0))
        parts = []
        while size := int(self.rfile.readline().split(b";")[0], 16):
            parts.append(self.rfile.read(size))
            self.rfile.readline()
        # The chunks end with an empty line, after any trailer fields.
        while self.rfile.readline().strip():
            pass
        return b"".join(parts)

    def starting(self) -> None:
        """The server's own answer while it starts: 503 and "Loading model"."""
        error = {"message": "Loading model", "type": "unavailable_error", "code": 503}
        body = json.dumps({"error": error}).encode()
        self.send_response_only(503, "Service Unavailable")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        """Writes nothing: the server's log has each request."""


def free_port() -> int:
    """A port on this computer that nothing listens at."""
    with socket.socket() as unused:
        unused.bind(("127.0.0.1", 0))
        return unused.getsockname()[1]


def in_use(port: int) -> bool:
    """Whether something on this computer already answers at the port."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def port_in_use(port: int) -> str:
    return (
        f"Port {port} is in use, perhaps by llama.cpp's server already running. Stop that, or run "
        f"uv run sulba.py model --port {port + 1}."
    )


def local() -> urllib.request.OpenerDirector:
    """An opener for addresses on this computer, which a proxy set for the internet can't reach."""
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def loading(
    process: subprocess.Popen[bytes], address: str, models: list[dict[str, Any]]
) -> list[str]:
    """Waits while the server loads the models, and returns the titles of those it hasn't loaded
    when it stops, fails to load one, or LOADING seconds pass: none once it has loaded them all."""
    titles = [model["title"] for model in models]
    deadline = time.monotonic() + LOADING
    statuses: dict[str, dict[str, Any]] = {}
    while time.monotonic() < deadline and process.poll() is None:
        try:
            with local().open(f"{address}/models", timeout=2) as response:
                statuses = {each["id"]: each["status"] for each in json.load(response)["data"]}
        except OSError, http.client.HTTPException:
            # Nothing listens at the address before the server starts.
            pass
        unloaded = [title for title in titles if statuses.get(title, {}).get("value") != "loaded"]
        if not unloaded or any(statuses.get(title, {}).get("failed") for title in unloaded):
            return unloaded
        time.sleep(0.25)
    return [title for title in titles if statuses.get(title, {}).get("value") != "loaded"]


def asked(address: str, models: list[dict[str, Any]]) -> int:
    """Asks each model one thing, by its kind, and shows what it answered: a chat model a question,
    an embedding model to embed a sentence, and a reranker to score two passages for a query."""
    for model in models:
        title, kind = model["title"], model["kind"]
        if kind == "chat":
            messages = [{"role": "user", "content": "Say hello."}]
            reply = posted(address, "chat/completions", title, messages=messages, max_tokens=32)
            usage = reply["usage"]
            print(f"{title} said: {reply['choices'][0]['message']['content']!r}")
            print(
                f"It read {usage['prompt_tokens']} tokens and wrote {usage['completion_tokens']}."
            )
        elif kind == "embedding":
            sentence = "The brakes stop the wheels."
            reply = posted(address, "embeddings", title, input=sentence)
            numbers = len(reply["data"][0]["embedding"])
            print(f"{title} embedded {sentence!r} as {numbers} numbers.")
        else:
            query = "Which part of a bicycle stops it?"
            passages = ["The brakes stop the wheels.", "The saddle is where the rider sits."]
            reply = posted(address, "rerank", title, query=query, documents=passages)
            print(f"{title} scored two passages for {query!r}:")
            for result in sorted(reply["results"], key=lambda result: -result["relevance_score"]):
                print(f"  {result['relevance_score']:.4f}  {passages[result['index']]}")
    return 0


def posted(address: str, path: str, model: str, **body: Any) -> dict[str, Any]:
    """The server's answer to a request for the model at its OpenAI-style path."""
    request = urllib.request.Request(
        f"{address}/v1/{path}",
        data=json.dumps({"model": model, **body}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with local().open(request, timeout=LOADING) as response:
        return json.load(response)


def stopped(log: Path) -> str:
    """Why the server stopped, from the end of what it wrote."""
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    return f"llama.cpp's server stopped. The last of what it wrote:\n{tail(lines)}"


def failed(log: Path, titles: list[str]) -> str:
    """Why the server didn't load the models, from the end of what it wrote."""
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    return (
        f"{listed(titles)} didn't load. The last of what llama.cpp's server wrote:\n{tail(lines)}"
    )


def tail(lines: list[str]) -> str:
    return "\n".join(f"  {line}" for line in lines[-10:])


def listed(names: list[str]) -> str:
    """Names as a sentence lists them, such as "A, B and C"."""
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def declared(response: http.client.HTTPResponse, start: int) -> int | None:
    """The size of the whole file as the publisher's answer gives it, if it does: the total in a
    part's Content-Range, or the Content-Length of all of it."""
    if start:
        total = response.headers.get("Content-Range", "").rpartition("/")[2]
    else:
        total = response.headers.get("Content-Length", "")
    return int(total) if total.isdigit() else None


def whole(path: Path, file: dict[str, Any]) -> bool:
    """Whether path holds the file: its size, then its sha256."""
    if not path.is_file() or path.stat().st_size != file["bytes"]:
        return False
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest() == file["sha256"]


def size(count: int) -> str:
    """A size in bytes as a download shows it, such as 26.4 MB."""
    for unit, scale in (("GB", 10**9), ("MB", 10**6), ("kB", 10**3)):
        if count >= scale:
            return f"{count / scale:.1f} {unit}"
    return f"{count} bytes"


def status_of(result: dict[str, Any]) -> str:
    """pass when every test passed, fail when one didn't, and error when none ran."""
    if result["problem"] or not result["tests"]:
        return "error"
    return "pass" if all(test["status"] == "pass" for test in result["tests"]) else "fail"


def split(
    stage: dict[str, Any], result: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """A run's tests, and apart from them, a Catch or Ship stage's checks."""
    ids = {check["id"] for check in stage["checks"]}
    ran = [] if result["problem"] else result["tests"]
    return (
        [test for test in ran if test["id"] not in ids],
        [test for test in ran if test["id"] in ids],
    )


def attempt(
    progress: dict[str, Any],
    stage: dict[str, Any],
    kind: str,
    tests: list[dict[str, Any]] | None,
    checks: list[dict[str, Any]] | None,
    review: dict[str, Any] | None,
) -> list[Any]:
    """An attempt as a link carries it: its id, the stage and its version, what happened, the
    seconds since the stage's last attempt, and when, with the learner's own day."""
    now = datetime.now(UTC)
    last = progress["last"]
    seconds = 0 if last is None else round(now.timestamp() - last)
    progress["last"] = now.timestamp()

    def count(ran: list[dict[str, Any]] | None) -> list[int] | None:
        if ran is None:
            return None
        return [sum(test["status"] == "pass" for test in ran), len(ran)]

    return [
        str(uuid.uuid4()),
        stage["id"],
        stage["version"],
        kind,
        count(tests),
        count(checks) if stage["checks"] else None,
        review,
        min(MAX_SECONDS, max(0, seconds)),
        now.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        now.astimezone().date().isoformat(),
    ]


def passed(progress: dict[str, Any], stage: dict[str, Any], review: dict[str, Any] | None) -> None:
    """Marks the stage done, with a Catch stage's review, and adds its pass to the attempts."""
    progress["passed"][stage["id"]] = review
    progress["attempts"].append(attempt(progress, stage, "pass", None, None, review))


def link(lab: dict[str, Any], progress: dict[str, Any]) -> str:
    """The lab's page, with the stages done here in its fragment, and the newest attempts since
    the last link that fit, the pass at least."""
    attempts = progress["attempts"][-MAX_ATTEMPTS:]
    address = linked(lab, progress["passed"], attempts)
    while len(address) > MAX_LINK and len(attempts) > 1:
        attempts = attempts[1:]
        address = linked(lab, progress["passed"], attempts)
    return address


def linked(lab: dict[str, Any], done: dict[str, Any], attempts: list[list[Any]]) -> str:
    payload = {"format": 1, "lab": lab["id"], "passed": done, "attempts": attempts}
    text = json.dumps(payload, separators=(",", ":")).encode()
    packed = zlib.compress(text, 9, wbits=-15)
    return f"{lab['page']}#run={base64.urlsafe_b64encode(packed).decode().rstrip('=')}"


def show_link(address: str) -> None:
    """Prints the link, and opens it when a person is at the terminal."""
    print("\nTo mark it done on the lab's page, open:\n")
    print(address)
    if sys.stdout.isatty():
        webbrowser.open_new_tab(address)


def following(lab: dict[str, Any], index: int) -> str:
    if index + 1 == len(lab["stages"]):
        return "\nThat was the lab's last stage."
    return f"\nStart stage {index + 2} with: uv run sulba.py next"


def start_next(lab: dict[str, Any], progress: dict[str, Any]) -> int:
    """Puts the next stage's starter in place: below the learner's code when an earlier stage
    made its file, or in a file of its own. After a Catch review that missed a problem, the lab
    goes on from the fixed code."""
    stages = lab["stages"]
    index = progress["stage"]
    stage = stages[index]
    if stage["id"] not in progress["passed"]:
        print(f"Stage {index + 1} isn't done yet. Run its tests with: uv run sulba.py")
        return 1
    if index + 1 == len(stages):
        print("That was the lab's last stage.")
        return 0
    review = progress["passed"][stage["id"]]
    if stage["kind"] == "catch" and review and len(review["caught"]) < review["problems"]:
        path = HERE / stage["file"]
        yours = path.with_name(f"{path.stem}.yours{path.suffix}")
        if path.is_file():
            path.replace(yours)
        path.write_text(decoded(stage["fixed"]), encoding="utf-8")
        print(f"The lab goes on from the fixed {stage['file']}. Yours is in {yours.name}.\n")
    upcoming = stages[index + 1]
    path = HERE / upcoming["file"]
    if any(each["file"] == upcoming["file"] for each in stages[: index + 1]):
        code = path.read_text(encoding="utf-8") if path.is_file() else ""
        path.write_text(add_starter(code, upcoming["starter"]), encoding="utf-8")
    elif path.exists():
        print(f"{upcoming['file']} is already here. Move it away, then run: uv run sulba.py next")
        return 1
    else:
        path.write_text(upcoming["starter"], encoding="utf-8")
    progress["stage"] = index + 1
    progress["last"] = datetime.now(UTC).timestamp()
    print(f"Stage {index + 2} of {len(stages)}: {upcoming['title']}")
    print(f"Its brief: {lab['page']}?stage={upcoming['slug']}")
    print(f"Work in {upcoming['file']}, then run its tests with: uv run sulba.py")
    return 0


def add_starter(code: str, starter: str) -> str:
    """The learner's code with a stage's starter added below it, as the lab's page adds it."""
    return f"{code.rstrip()}\n\n\n{starter}"


def report(stage: dict[str, Any], result: dict[str, Any]) -> None:
    """The run's results, as the lab's page shows them."""
    problem = result["problem"]
    if problem:
        print(f"{problem['kind']}: {problem['message']}")
        where(problem.get("location"))
        print("\nYour code has an error. Fix it, then run the tests again.")
        show_output(result["output"], [])
        return
    tests, checks = split(stage, result)
    if stage["kind"] == "catch":
        print(catch_summary(tests, checks))
        print("\nThe assistant's tests")
        for test in tests:
            line(test, detail=True)
        show_output(result["output"], tests)
    elif stage["kind"] == "ship":
        print(f"{counted(tests, 'test', 'tests')} {counted(checks, 'check', 'checks')}")
        print("\nTests")
        for test in tests:
            line(test, detail=False)
        print("\nBefore it ships")
        for check in stage["checks"]:
            ran = next((test for test in checks if test["id"] == check["id"]), None)
            ok = ran is not None and ran["status"] == "pass"
            print(f"  {mark(ok)} {check['title']}")
            print(f"      {check['requires']}")
            if ran is not None and not ok:
                print(f"      {check['failure']}")
            if ran is not None and ran["note"]:
                print(f"      {ran['note']}")
        show_output(result["output"], [])
    else:
        print(counted(tests, "test", "tests"))
        print()
        for test in tests:
            line(test, detail=True)
        show_output(result["output"], tests)


def mark(passed: bool) -> str:
    return "✓" if passed else "✗"


def line(test: dict[str, Any], *, detail: bool) -> None:
    ok = test["status"] == "pass"
    print(f"  {mark(ok)} {test['name']}")
    if ok or not detail:
        return
    if test["message"]:
        print(indented(test["message"]))
    if test["expected"] is not None and test["actual"] is not None:
        print(indented(f"Expected: {test['expected']}"))
        print(indented(f"Got:      {test['actual']}"))
    where(test["location"])


def where(location: dict[str, Any] | None) -> None:
    if location:
        print(indented(f"{location['file']}, line {location['line']}"))


def indented(text: str) -> str:
    return "\n".join(f"      {part}" for part in text.splitlines())


def show_output(loading: str, tests: list[dict[str, Any]]) -> None:
    """What the code printed while it loaded, and in each test shown."""
    printed = [("While loading", loading)] + [(test["name"], test["output"]) for test in tests]
    printed = [(name, text) for name, text in printed if text.strip()]
    if not printed:
        return
    print("\nOutput")
    for name, text in printed:
        print(f"  {name}")
        print(indented(text.rstrip()))


def counted(tests: list[dict[str, Any]], one: str, many: str) -> str:
    """How many of some tests or checks passed, such as "All 3 tests passed." """
    ok = sum(test["status"] == "pass" for test in tests)
    if len(tests) == 1:
        return f"The {one} {'passed' if ok else 'failed'}."
    if ok < len(tests):
        return f"{ok} of {len(tests)} {many} passed."
    return f"Both {many} passed." if len(tests) == 2 else f"All {len(tests)} {many} passed."


def catch_summary(tests: list[dict[str, Any]], checks: list[dict[str, Any]]) -> str:
    """How many production checks passed, then how the assistant's own tests did."""
    caught = sum(check["status"] == "pass" for check in checks)
    checked = (
        f"The production check {'passed' if caught else 'failed'}."
        if len(checks) == 1
        else f"{caught} of {len(checks)} production checks passed."
    )
    ok = sum(test["status"] == "pass" for test in tests)
    tested = (
        f"The assistant's {'test' if len(tests) == 1 else 'tests'} passed."
        if ok == len(tests)
        else f"{ok} of the assistant's {len(tests)} tests passed."
    )
    return f"{checked} {tested}"


if __name__ == "__main__":
    # A terminal that can't show a character shows a stand-in rather than stopping the run.
    sys.stdout.reconfigure(errors="replace")
    sys.exit(main(sys.argv[1:]))

"""Runs a session's tests and reports one result per test.

The browser calls run() in Pyodide and the sulba command calls it in CPython, so a test reports
the same way wherever it runs. Arguments and the result are JSON text, which crosses from
JavaScript into Python without conversion.
"""

from __future__ import annotations

import ast
import gc
import importlib
import io
import json
import math
import os
import shutil
import sys
import tempfile
import time
from contextlib import chdir, redirect_stderr, redirect_stdout, suppress
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

import sulba_fixtures
from sulba_fixtures import cache_folder, check_types, fetched_package

# The longest value or message a result carries. A failed check on a large array would
# otherwise send all of it.
LIMIT = 1000
# The release of Node.js that runs a session's TypeScript tests on the learner's machine (decision
# record 39), where its releases are, and its build for each system, by the names Python gives the
# system and the machine: the build's archive, its size and its sha256.
NODE = "24.22.1"
NODE_RELEASES = "https://nodejs.org/dist"
NODE_BUILDS = {
    ("Windows", "AMD64"): (
        "win-x64.zip",
        37748064,
        "d2046d28c2c3dcd211ac5145c0bf30e2047ef9dfb306693c8c6e2eccd8b95fa5",
    ),
    ("Windows", "ARM64"): (
        "win-arm64.zip",
        33786263,
        "a0c807319fede24c4a0d8f84564c82a619bd313b16b10c007c383c2609e99171",
    ),
    ("Darwin", "arm64"): (
        "darwin-arm64.tar.gz",
        53062778,
        "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7",
    ),
    ("Darwin", "x86_64"): (
        "darwin-x64.tar.gz",
        54382566,
        "d132557e7ee2b85af08b0c8c34338e65c6430f2238d01f727728ef42dc83b035",
    ),
    ("Linux", "x86_64"): (
        "linux-x64.tar.xz",
        32026916,
        "6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6",
    ),
    ("Linux", "aarch64"): (
        "linux-arm64.tar.xz",
        30978868,
        "dbabf7a1cbf947e6059ffad2c27b80041db97dea1e553b62afdee7f13fca336e",
    ),
}
# The reporter Node's test runner writes each result with, as a line of JSON.
REPORTER = Path(__file__).with_name("sulba_reporter.mjs")
# The release of Go that runs a session's Go tests on the learner's machine (decision record 43),
# where its archives are, which go.dev/dl links to, and its archive for each system, by the names
# Python gives the system and the machine: the archive's name, its size and its sha256.
GO = "1.27.3"
GO_RELEASES = "https://dl.google.com/go"
GO_BUILDS = {
    ("Windows", "AMD64"): (
        "windows-amd64.zip",
        79010309,
        "f26081f438319757f8a1b46d7d0b2c5ec7583d4038e485e0aa725cfde7885fff",
    ),
    ("Windows", "ARM64"): (
        "windows-arm64.zip",
        75113075,
        "c507872ff21f8a7cd3c1c217b059c6f7271a4a9d8e692810ef9dd3e1f601197c",
    ),
    ("Darwin", "arm64"): (
        "darwin-arm64.tar.gz",
        68196737,
        "dd3908cf20959d798c1e06ebe5b72213f0505ce01373b40ce3110975a6cd99c2",
    ),
    ("Darwin", "x86_64"): (
        "darwin-amd64.tar.gz",
        71697771,
        "b6f8e931e4ab497fcde6da8ae4499a58f9d258e55c8a80824a516eae5950a750",
    ),
    ("Linux", "x86_64"): (
        "linux-amd64.tar.gz",
        70588678,
        "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40",
    ),
    ("Linux", "aarch64"): (
        "linux-arm64.tar.gz",
        67076044,
        "a06e99309dbcbdca1a8ccd2282c3ee146e55930886e26b4f1193269587165f49",
    ),
}

# The JDK that compiles and runs a session's Java on the learner's machine (decision record 45):
# Liberica JDK Lite, where BellSoft publishes it, and its archive for each system, by the names
# Python gives the system and the machine: the archive's name, its size and its sha256.
JAVA = "25.0.5.0.2+5"
JAVA_RELEASES = "https://github.com/bell-sw/Liberica/releases/download"
JAVA_BUILDS = {
    ("Windows", "AMD64"): (
        "windows-amd64-lite.zip",
        82885946,
        "35218d3407607b170eeb6e8b048b46aac4e287d64b0d23691b5c5d5b3b8c7ea2",
    ),
    ("Windows", "ARM64"): (
        "windows-aarch64-lite.zip",
        80303853,
        "9fad7d8935ccb22de5a5c0b182a71bea53ab5eeb40ff42775badc99a31d66de4",
    ),
    ("Darwin", "arm64"): (
        "macos-aarch64-lite.tar.gz",
        80507572,
        "63a6b768183133d2acc87dcf5f4142185baa1aadf6b5d68267d840d7c694b729",
    ),
    ("Darwin", "x86_64"): (
        "macos-amd64-lite.tar.gz",
        81646190,
        "0b461ac569ccfd733727b8ddafa78835bedbfa3ccfc9fba2fb2e47cf2ec6da82",
    ),
    ("Linux", "x86_64"): (
        "linux-amd64-lite.tar.gz",
        83098331,
        "1017bff21d11331f652cc219403b43b63c139f040a32cea1770139fbfb474aeb",
    ),
    ("Linux", "aarch64"): (
        "linux-aarch64-lite.tar.gz",
        82325521,
        "d9e6bec48560f986848efd5c4a4540130291dd9c67ea9e2df0de5964426dda20",
    ),
}
# The jars a Java run has, from Maven Central, each by its path there, its size and its sha256:
# JUnit's console launcher, which runs the tests, and Jackson, which every run's classes can use.
MAVEN = "https://repo1.maven.org/maven2"
JUNIT = (
    "org/junit/platform/junit-platform-console-standalone/6.1.3/"
    "junit-platform-console-standalone-6.1.3.jar",
    2997949,
    "e62b96ac475dbcde8599ea905d088f65d90778f86e259b856a49fa5c4ea256ec",
)
JACKSON = [
    (
        "tools/jackson/core/jackson-databind/3.2.4/jackson-databind-3.2.4.jar",
        1990007,
        "c4af37223d5024f1294a5450598b01b65f30c53d9e906f02c3955ba1fb14a67d",
    ),
    (
        "tools/jackson/core/jackson-core/3.2.4/jackson-core-3.2.4.jar",
        613344,
        "494b9f5fccf008042d5a72c5bf00629b144c0ba7362a9864cbb02234c9772651",
    ),
    (
        "com/fasterxml/jackson/core/jackson-annotations/2.22/jackson-annotations-2.22.jar",
        84211,
        "21ddb598807d3a51a876704eb979d9296e1c6a6f47ab1826ff88c6d6a127a2d0",
    ),
]


def run(files_json: str, tests_json: str, links_json: str = "{}") -> str:
    """Write the files to a new folder, with the linked files beside them, run the test files
    there, and return the result. Python's tests run with pytest, TypeScript's with Node, Go's
    with Go and Java's with JUnit, and a run with more than one gives the results of each."""
    files: dict[str, str] = json.loads(files_json)
    tests: list[str] = json.loads(tests_json)
    links: dict[str, str] = json.loads(links_json)
    scripts = [name for name in tests if name.endswith(".ts")]
    go = [name for name in tests if name.endswith(".go")]
    java = [name for name in tests if name.endswith(".java")]
    python = [name for name in tests if not name.endswith((".ts", ".go", ".java"))]
    results = []
    if python or not (scripts or go or java):
        results.append(pytest_run(files, python, links))
    if scripts:
        results.append(typescript(files, scripts, links))
    if go:
        results.append(go_run(files, go, links))
    if java:
        results.append(java_run(files, java, links))
    problem = next((result["problem"] for result in results if result["problem"]), None)
    return json.dumps(
        {
            "tests": [] if problem else [test for result in results for test in result["tests"]],
            "problem": problem,
            "output": "".join(result["output"] for result in results),
            "durationMs": sum(result["durationMs"] for result in results),
        }
    )


def pytest_run(files: dict[str, str], tests: list[str], links: dict[str, str]) -> dict[str, Any]:
    """Run the Python test files with pytest."""
    with session_folder() as folder:
        # An empty config file beside the session, so pytest never picks up one from a folder
        # above it.
        config = Path(folder, "pytest.ini")
        config.write_text("[pytest]\n", encoding="utf-8")
        root = Path(folder, "session").resolve()
        write(root, files)
        link(root, links)
        report = Report(root)
        started = time.perf_counter()
        # The fixtures are a plugin of their own, so a run inside a test can load them too.
        plugins = [report, sulba_fixtures]
        exit_code = within(root, lambda: pytest.main(arguments(tests, config), plugins=plugins))
        result = report.result(int(exit_code))
        result["durationMs"] = round((time.perf_counter() - started) * 1000)
    return result


def typescript(files: dict[str, str], tests: list[str], links: dict[str, str]) -> dict[str, Any]:
    """Run TypeScript tests with Node's test runner, once tsc finds no error in the session's
    files (decision record 39). A session's packages are those its package-lock.json pins, and
    the session runs in a folder inside theirs, where Node and tsc find them."""
    import subprocess

    try:
        node, npm = node_program()
        packages = node_packages(node, npm, files)
    except RuntimeError as error:
        return {
            "tests": [],
            "problem": {"kind": "RunError", "message": clip(str(error)), "location": None},
            "output": "",
            "durationMs": 0,
        }
    runs = packages / "runs"
    runs.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sulba-", dir=runs, ignore_cleanup_errors=True) as at:
        root = Path(at, "session").resolve()
        write(root, files)
        link(root, links)
        started = time.perf_counter()
        tsc = packages / "node_modules" / "typescript" / "bin" / "tsc"
        checked = subprocess.run(
            [node, tsc, "-p", ".", "--pretty", "false"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if checked.returncode != 0:
            result = type_errors(checked.stdout + checked.stderr, root)
        else:
            ran = subprocess.run(
                [node, "--test", f"--test-reporter={REPORTER.as_uri()}", *tests],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            result = reported(ran.stdout, ran.stderr, root, tests)
        result["durationMs"] = round((time.perf_counter() - started) * 1000)
    return result


def fetches_first(files: dict[str, str]) -> bool:
    """Whether a TypeScript run of these files fetches Node.js or the packages it pins first."""
    try:
        node, _ = node_files(node_place()[1])
        packages = packages_folder(files)
    except RuntimeError:
        # The run stops before it fetches anything, and says why.
        return False
    return not (node.is_file() and (packages / "node_modules").is_dir())


def node_place() -> tuple[tuple[str, int, str], Path]:
    """Node.js's build for this system, and the folder of the cache folder it's unpacked into,
    named as the build's own folder is."""
    import platform

    system, machine = platform.system(), platform.machine()
    if (system, machine) not in NODE_BUILDS:
        raise RuntimeError(f"Node.js {NODE} has no build for {system} on {machine}.")
    build = NODE_BUILDS[(system, machine)]
    return build, cache_folder() / "node" / f"node-v{NODE}-{build[0].split('.')[0]}"


def node_files(folder: Path) -> tuple[Path, Path]:
    """Node.js and the script that runs npm, in the folder of a build of Node.js."""
    if os.name == "nt":
        return folder / "node.exe", folder / "node_modules" / "npm" / "bin" / "npm-cli.js"
    return folder / "bin" / "node", folder / "lib" / "node_modules" / "npm" / "bin" / "npm-cli.js"


def node_program() -> tuple[Path, Path]:
    """Node.js, and the script that runs npm, from Node's build for this system, fetched into the
    cache folder the first time."""
    import io
    import tarfile
    import zipfile

    (archive, size, sha256), folder = node_place()
    node, npm = node_files(folder)
    if node.is_file():
        return node, npm
    name = f"node-v{NODE}-{archive}"
    packed = fetched_package(f"{NODE_RELEASES}/v{NODE}/{name}", size, sha256, "Node.js")
    folder.parent.mkdir(parents=True, exist_ok=True)
    # Unpacked beside its place first, so a run stopped halfway leaves no Node.js to find.
    unpacking = Path(tempfile.mkdtemp(dir=folder.parent))
    try:
        if archive.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(packed)) as files:
                files.extractall(unpacking)
        else:
            with tarfile.open(fileobj=io.BytesIO(packed)) as files:
                files.extractall(unpacking, filter="data")
        try:
            os.replace(unpacking / folder.name, folder)
        except OSError:
            # Another run put it there first.
            if not node.is_file():
                raise
    finally:
        shutil.rmtree(unpacking, ignore_errors=True)
    return node, npm


def node_packages(node: Path, npm: Path, files: dict[str, str]) -> Path:
    """The folder whose node_modules holds the packages the session's package-lock.json pins,
    installed with npm into the cache folder the first time, without running their scripts."""
    import subprocess

    folder = packages_folder(files)
    if (folder / "node_modules").is_dir():
        return folder
    folder.parent.mkdir(parents=True, exist_ok=True)
    installing = Path(tempfile.mkdtemp(dir=folder.parent))
    try:
        write(installing, {name: files[name] for name in ("package.json", "package-lock.json")})
        # npm keeps what it fetches in the cache folder too.
        installed = subprocess.run(
            [
                node,
                npm,
                "ci",
                "--ignore-scripts",
                "--no-audit",
                "--no-fund",
                "--no-update-notifier",
                "--loglevel=error",
                f"--cache={folder.parent / 'cache'}",
            ],
            cwd=installing,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if installed.returncode != 0:
            said = (installed.stderr or installed.stdout).strip().splitlines()
            raise RuntimeError("npm didn't install the lab's packages: " + " ".join(said[-3:]))
        try:
            os.replace(installing, folder)
        except OSError:
            # Another run put them there first.
            if not (folder / "node_modules").is_dir():
                raise
    finally:
        shutil.rmtree(installing, ignore_errors=True)
    return folder


def packages_folder(files: dict[str, str]) -> Path:
    """Where the packages the session's package.json and package-lock.json pin are installed, in
    a folder of the cache folder named for the two."""
    import hashlib

    manifest, lock = files.get("package.json"), files.get("package-lock.json")
    if manifest is None or lock is None:
        raise RuntimeError("A TypeScript run needs the lab's package.json and package-lock.json.")
    pinned = hashlib.sha256(f"{NODE}\0{manifest}\0{lock}".encode()).hexdigest()
    return cache_folder() / "npm" / pinned


def type_errors(printed: str, root: Path) -> dict[str, Any]:
    """tsc's first error as the run's problem, with every error it found as the run's output."""
    import re

    lines = printed.splitlines()
    for line in lines:
        found = re.match(r"^(.+)\((\d+),\d+\): error (TS\d+): (.*)$", line)
        if found:
            problem = {
                "kind": found[3],
                "message": clip(found[4]),
                "location": {"file": found[1], "line": int(found[2])},
            }
            break
    else:
        said = printed.strip() or "tsc stopped without saying why."
        problem = {"kind": "RunError", "message": clip(said), "location": None}
    return {"tests": [], "problem": problem, "output": cleaned(printed, root)}


def reported(printed: str, errors: str, root: Path, tests: list[str]) -> dict[str, Any]:
    """The run's result from the reporter's lines: each test's, in the order of their files, the
    error that stopped a file loading, and what the tests printed."""
    import re

    results: list[dict[str, Any]] = []
    problem: dict[str, Any] | None = None
    output = ""
    for line in printed.splitlines():
        if not line.startswith("{"):
            continue
        event = json.loads(line)
        if event["kind"] == "output":
            output += event["text"]
        elif event["kind"] == "problem":
            problem = problem or event["problem"]
        else:
            results.append(event)
    if problem is None and not results:
        said = errors.strip() or "No tests ran."
        problem = {"kind": "RunError", "message": clip(cleaned(said, root)), "location": None}
    if problem is not None:
        problem["message"] = clip(cleaned(problem["message"], root))
        return {"tests": [], "problem": problem, "output": cleaned(output, root)}
    order = {name: index for index, name in enumerate(tests)}
    results.sort(key=lambda result: order.get(result["file"], len(order)))
    entries = []
    for result in results:
        # A test's name starts with its permanent id, as in "tst_abc123 Finds the user".
        named = re.fullmatch(r"(tst_[0-9a-z]{6}) (.+)", result["name"], re.DOTALL)
        entries.append(
            {
                "id": named[1] if named else None,
                "name": named[2] if named else result["name"],
                "status": result["status"],
                "message": None
                if result["message"] is None
                else clip(cleaned(result["message"], root)),
                "expected": None if result["expected"] is None else clip(result["expected"]),
                "actual": None if result["actual"] is None else clip(result["actual"]),
                "location": result["location"],
                "output": "",
                "note": None,
                "durationMs": result["durationMs"],
            }
        )
    return {"tests": entries, "problem": None, "output": cleaned(output, root)}


def go_run(files: dict[str, str], tests: list[str], links: dict[str, str]) -> dict[str, Any]:
    """Run Go tests with go test (decision record 43): each folder of test files is a package of
    its own, which imports the learner's from the lab's go.mod. Of the test files in tests/, only
    those the run names are written, so a test file the run leaves out doesn't build with it; the
    learner's own tests, beside their files, are their code."""
    import subprocess

    try:
        go = go_program()
    except RuntimeError as error:
        return {
            "tests": [],
            "problem": {"kind": "RunError", "message": clip(str(error)), "location": None},
            "output": "",
            "durationMs": 0,
        }
    if "go.mod" not in files:
        problem = {
            "kind": "RunError",
            "message": "A Go run needs the lab's go.mod.",
            "location": None,
        }
        return {"tests": [], "problem": problem, "output": "", "durationMs": 0}
    written = {
        name: text
        for name, text in files.items()
        if name in tests or not (name.startswith("tests/") and name.endswith("_test.go"))
    }
    packages = sorted({f"./{PurePosixPath(name).parent}" for name in tests})
    with session_folder() as folder:
        root = Path(folder, "session").resolve()
        write(root, written)
        link(root, links)
        started = time.perf_counter()
        # go test vets only the packages it tests, and the learner's are the ones the tests
        # import, so go vet checks every package first, and builds them as it does.
        vetted = subprocess.run(
            [go, "vet", "./..."],
            cwd=root,
            env=go_environment(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if vetted.returncode != 0:
            said = vetted.stdout + vetted.stderr
            result = {
                "tests": [],
                "problem": go_build_problem(said, root),
                "output": cleaned(said, root),
            }
        else:
            ran = subprocess.run(
                [go, "test", "-json", "-count=1", *packages],
                cwd=root,
                env=go_environment(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            named = {name: files[name] for name in tests}
            result = go_reported(ran.stdout, ran.stderr, root, named)
        result["durationMs"] = round((time.perf_counter() - started) * 1000)
    return result


def go_environment() -> dict[str, str]:
    """A Go run's environment: the Go the runner pins and nothing it would fetch, no C compiler,
    none of the learner's own go env settings, and the build cache in the cache folder."""
    folder = cache_folder() / "go"
    return {
        **os.environ,
        "GOTOOLCHAIN": "local",
        "GOPROXY": "off",
        "GOENV": "off",
        "GOFLAGS": "",
        "CGO_ENABLED": "0",
        "GOPATH": str(folder / "path"),
        "GOCACHE": str(folder / "build"),
    }


def go_place() -> tuple[tuple[str, int, str], Path]:
    """Go's archive for this system, and the folder of the cache folder it's unpacked into, named
    for the release and the system."""
    import platform

    system, machine = platform.system(), platform.machine()
    if (system, machine) not in GO_BUILDS:
        raise RuntimeError(f"Go {GO} has no build for {system} on {machine}.")
    build = GO_BUILDS[(system, machine)]
    return build, cache_folder() / "go" / f"go{GO}.{build[0].split('.')[0]}"


def go_program() -> Path:
    """The go command, from Go's archive for this system, fetched into the cache folder the first
    time."""
    import io
    import tarfile
    import zipfile

    (archive, size, sha256), folder = go_place()
    go = folder / "bin" / ("go.exe" if os.name == "nt" else "go")
    if go.is_file():
        return go
    packed = fetched_package(f"{GO_RELEASES}/go{GO}.{archive}", size, sha256, "Go")
    folder.parent.mkdir(parents=True, exist_ok=True)
    # Unpacked beside its place first, so a run stopped halfway leaves no Go to find.
    unpacking = Path(tempfile.mkdtemp(dir=folder.parent))
    try:
        if archive.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(packed)) as files:
                files.extractall(unpacking)
        else:
            with tarfile.open(fileobj=io.BytesIO(packed)) as files:
                files.extractall(unpacking, filter="tar")
        try:
            os.replace(unpacking / "go", folder)
        except OSError:
            # Another run put it there first.
            if not go.is_file():
                raise
    finally:
        shutil.rmtree(unpacking, ignore_errors=True)
    return go


def go_fetches_first() -> bool:
    """Whether a Go run fetches Go first."""
    try:
        _, folder = go_place()
    except RuntimeError:
        # The run stops before it fetches anything, and says why.
        return False
    return not (folder / "bin" / ("go.exe" if os.name == "nt" else "go")).is_file()


def go_reported(printed: str, errors: str, root: Path, tests: dict[str, str]) -> dict[str, Any]:
    """The run's result from go test's events: each named test's, in the order of its files, a
    package that didn't build as the run's problem, and what the tests printed. A test that never
    ran, because one before it in its package panicked, is an error too."""
    import re

    events = [json.loads(line) for line in printed.splitlines() if line.startswith("{")]
    built = "".join(
        event.get("Output", "") for event in events if event["Action"] == "build-output"
    )
    if built:
        return {
            "tests": [],
            "problem": go_build_problem(built, root),
            "output": cleaned(built, root),
        }
    named: dict[str, str] = {}
    for text in tests.values():
        for found in re.finditer(r'\bt\.Run\(\s*"(tst_[0-9a-z]{6}) ([^"]*)"', text):
            named.setdefault(found[1], found[2])
    # By package and test: go test runs the packages at once, so their events interleave, and two
    # packages may each have a test of the same name.
    outputs: dict[tuple[str, str], str] = {}
    ended: dict[tuple[str, str], dict[str, Any]] = {}
    failed: dict[str, str] = {}
    panicked: dict[str, str] = {}
    output = ""
    for event in events:
        package, test = event.get("Package", ""), event.get("Test")
        if event["Action"] == "output" and test:
            said = event["Output"]
            # A panic's message and stack come after the failure of the test that panicked, as
            # output of the test it runs in.
            if package not in panicked and package in failed and said.startswith("panic: "):
                panicked[package] = failed[package]
            owner = panicked.get(package, "")
            key = (package, owner if owner.split("/")[0] == test else test)
            outputs[key] = outputs.get(key, "") + said
            if event.get("OutputType") not in ("frame", "error", "error-continue"):
                output += said
        elif event["Action"] in ("pass", "fail", "skip") and test:
            ended[(package, test)] = event
            if event["Action"] == "fail" and "/" in test:
                failed[package] = test
    entries = []
    for id, name in named.items():
        key = next((each for each in ended if re.search(rf"/{id}_", each[1])), ("", ""))
        entries.append(go_entry(id, name, ended.get(key), outputs.get(key, ""), root))
    if not entries and not ended:
        said = (errors or printed).strip() or "No tests ran."
        problem = {"kind": "RunError", "message": clip(cleaned(said, root)), "location": None}
        return {"tests": [], "problem": problem, "output": cleaned(output, root)}
    return {"tests": entries, "problem": None, "output": cleaned(output, root)}


def go_entry(
    id: str, name: str, ended: dict[str, Any] | None, printed: str, root: Path
) -> dict[str, Any]:
    """A Go test's result: a failure's first message, a panic as an error with the deepest line
    of the session's own code, outside its tests, that it passed, and a test that never ran."""
    import re

    entry: dict[str, Any] = {
        "id": id,
        "name": name,
        "status": "pass",
        "message": None,
        "expected": None,
        "actual": None,
        "location": None,
        "output": "",
        "note": None,
        "durationMs": round((ended or {}).get("Elapsed", 0) * 1000),
    }
    panicked = re.search(r"^panic: (.+?)(?: \[recovered[^\]]*\])?$", printed, re.MULTILINE)
    if panicked:
        entry["status"] = "error"
        entry["message"] = clip(f"panic: {panicked[1]}")
        entry["location"] = go_location(printed, root)
    elif ended is None:
        entry["status"] = "error"
        entry["message"] = "Didn't run: a test before it in its package panicked."
    elif ended["Action"] == "fail":
        entry["status"] = "fail"
        said = re.search(r"^\s+\S+?\.go:\d+: (.+)$", printed, re.MULTILINE)
        entry["message"] = clip(said[1] if said else "The check failed.")
    elif ended["Action"] == "skip":
        entry["status"] = "skip"
    return entry


def go_location(printed: str, root: Path) -> dict[str, Any] | None:
    """The first line of a panic's stack in the session's own files, outside its tests: the
    stack starts where the panic did."""
    import re

    for found in re.finditer(r"^\s+(.+\.go):(\d+)", printed, re.MULTILINE):
        path = Path(found[1])
        if path.is_relative_to(root):
            file = path.relative_to(root).as_posix()
            if not file.startswith("tests/"):
                return {"file": file, "line": int(found[2])}
    return None


def go_build_problem(built: str, root: Path) -> dict[str, Any]:
    """The first error as the run's problem: the compiler's, under the name of the package that
    didn't build, which vet marks as its own when it finds it, or else vet's."""
    import re

    building = False
    for line in built.splitlines():
        building = building or line.startswith("# ")
        found = re.match(r"^(?:vet: )?(?:\.[/\\])?(.+?\.go):(\d+):(?:\d+:)? (.+)$", line.strip())
        if found:
            file = cleaned(found[1], root).replace(os.sep, "/")
            return {
                "kind": "BuildError" if building else "VetError",
                "message": clip(found[3]),
                "location": {"file": file, "line": int(found[2])},
            }
    said = built.strip() or "Go stopped without saying why."
    return {"kind": "BuildError", "message": clip(cleaned(said, root)), "location": None}


def java_run(files: dict[str, str], tests: list[str], links: dict[str, str]) -> dict[str, Any]:
    """Compile the session's Java with javac and run its tests with JUnit's console launcher
    (decision record 45): the learner's classes, the lab's and the tests share Java's unnamed
    package. Of the test files in tests/, only those the run names are compiled, so a test file
    the run leaves out doesn't build with it."""
    import subprocess

    try:
        home, junit, jackson = java_toolkit()
    except RuntimeError as error:
        return {
            "tests": [],
            "problem": {"kind": "RunError", "message": clip(str(error)), "location": None},
            "output": "",
            "durationMs": 0,
        }
    sources = sorted(
        name for name in files if name.endswith(".java") and not name.startswith("tests/")
    )
    libraries = os.pathsep.join(str(each) for each in jackson)
    with session_folder() as folder:
        root = Path(folder, "session").resolve()
        write(root, files)
        link(root, links)
        started = time.perf_counter()
        javac = str(home / "bin" / ("javac.exe" if os.name == "nt" else "javac"))

        def compiled(
            output: str, classes: str, names: list[str]
        ) -> subprocess.CompletedProcess[str]:
            # Relative paths, so javac names each file as the learner sees it.
            return subprocess.run(
                [javac, "-encoding", "UTF-8", "-d", output, "-cp", classes, *names],
                cwd=root,
                env=java_environment(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

        built = compiled("out/main", libraries, sources) if sources else None
        if built is not None and built.returncode != 0:
            result = {
                "tests": [],
                "problem": java_build_problem(built.stderr, root),
                "output": cleaned(built.stderr, root),
            }
        else:
            classes = os.pathsep.join(["out/main", libraries, str(junit)])
            checked = compiled("out/tests", classes, tests)
            if checked.returncode != 0:
                result = {
                    "tests": [],
                    "problem": java_build_problem(checked.stderr, root),
                    "output": cleaned(checked.stderr, root),
                }
            else:
                ran = subprocess.run(
                    [
                        str(home / "bin" / ("java.exe" if os.name == "nt" else "java")),
                        "-Dstdout.encoding=UTF-8",
                        "-Dstderr.encoding=UTF-8",
                        "-jar",
                        str(junit),
                        "execute",
                        "--class-path",
                        os.pathsep.join(["out/main", "out/tests", libraries]),
                        "--scan-class-path",
                        "out/tests",
                        "--reports-dir",
                        "out/reports",
                        "--redirect-stdout=out/printed.txt",
                        "--redirect-stderr=out/printed.txt",
                        "--details=none",
                        "--disable-banner",
                        "--disable-ansi-colors",
                    ],
                    cwd=root,
                    env=java_environment(),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                named = {name: files[name] for name in tests}
                result = java_reported(root, ran.stdout + ran.stderr, named, sources)
        result["durationMs"] = round((time.perf_counter() - started) * 1000)
    return result


def java_environment() -> dict[str, str]:
    """A Java run's environment: none of the learner's own settings for the JVM or the class
    path."""
    left_out = {"JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "CLASSPATH"}
    return {name: value for name, value in os.environ.items() if name not in left_out}


def java_place() -> tuple[tuple[str, int, str], Path]:
    """The JDK's archive for this system, and the folder of the cache folder it's unpacked into,
    named for the release and the system."""
    import platform

    system, machine = platform.system(), platform.machine()
    if (system, machine) not in JAVA_BUILDS:
        raise RuntimeError(f"Liberica JDK {JAVA} has no build for {system} on {machine}.")
    build = JAVA_BUILDS[(system, machine)]
    return build, cache_folder() / "java" / f"jdk-{JAVA}-{build[0].split('.')[0]}"


def java_toolkit() -> tuple[Path, Path, list[Path]]:
    """The JDK's home, JUnit's console launcher and Jackson's jars, each fetched into the cache
    folder the first time."""
    import io
    import tarfile
    import zipfile

    (archive, size, sha256), home = java_place()
    if not (home / "bin").is_dir():
        packed = fetched_package(
            f"{JAVA_RELEASES}/{JAVA}/bellsoft-jdk{JAVA}-{archive}", size, sha256, "JDK"
        )
        home.parent.mkdir(parents=True, exist_ok=True)
        # Unpacked beside its place first, so a run stopped halfway leaves no JDK to find.
        unpacking = Path(tempfile.mkdtemp(dir=home.parent))
        try:
            if archive.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(packed)) as files:
                    files.extractall(unpacking)
            else:
                with tarfile.open(fileobj=io.BytesIO(packed)) as files:
                    files.extractall(unpacking, filter="tar")
            # The JDK's home is the folder with bin/javac in it, which on macOS is Contents/Home.
            javac = next(unpacking.rglob("javac" if os.name != "nt" else "javac.exe"))
            if os.name != "nt" and not os.access(javac, os.X_OK):
                raise RuntimeError("The JDK's javac can't be run.")
            try:
                os.replace(javac.parent.parent, home)
            except OSError:
                # Another run put it there first.
                if not (home / "bin").is_dir():
                    raise
        finally:
            shutil.rmtree(unpacking, ignore_errors=True)
    jars = [java_jar(path, size, sha256) for path, size, sha256 in [JUNIT, *JACKSON]]
    return home, jars[0], jars[1:]


def java_jar(path: str, size: int, sha256: str) -> Path:
    """A jar from Maven Central, in the cache folder, fetched there the first time."""
    jar = cache_folder() / "java" / "jars" / PurePosixPath(path).name
    if not jar.is_file():
        packed = fetched_package(f"{MAVEN}/{path}", size, sha256, PurePosixPath(path).name)
        jar.parent.mkdir(parents=True, exist_ok=True)
        # Written beside its place first, so a run stopped halfway leaves no jar to find.
        writing = jar.with_name(f"{jar.name}.{os.getpid()}")
        writing.write_bytes(packed)
        os.replace(writing, jar)
    return jar


def java_fetches_first() -> bool:
    """Whether a Java run fetches the JDK or a jar first."""
    try:
        _, home = java_place()
    except RuntimeError:
        # The run stops before it fetches anything, and says why.
        return False
    jars = home.parent / "jars"
    return not (home / "bin").is_dir() or not all(
        (jars / PurePosixPath(path).name).is_file() for path, _, _ in [JUNIT, *JACKSON]
    )


def java_reported(
    root: Path, printed: str, tests: dict[str, str], sources: list[str]
) -> dict[str, Any]:
    """The run's result from JUnit's XML report: each named test's, in the order of its files,
    with what the tests printed, which the launcher writes to a file of its own."""
    import re
    from xml.etree import ElementTree

    named: dict[str, str] = {}
    for text in tests.values():
        for found in re.finditer(r'@DisplayName\(\s*"(tst_[0-9a-z]{6}) ([^"]*)"', text):
            named.setdefault(found[1], found[2])
    cases: dict[str, ElementTree.Element] = {}
    for report in sorted((root / "out" / "reports").glob("TEST-*.xml")):
        for case in ElementTree.parse(report).iter("testcase"):
            said = case.findtext("system-out") or ""
            found = re.search(r"^display-name: .* > (tst_[0-9a-z]{6}) ", said, re.MULTILINE)
            if found:
                cases[found[1]] = case
    written = root / "out" / "printed.txt"
    output = written.read_text(encoding="utf-8", errors="replace") if written.is_file() else ""
    if not cases:
        said = printed.strip() or "No tests ran."
        problem = {"kind": "RunError", "message": clip(cleaned(said, root)), "location": None}
        return {"tests": [], "problem": problem, "output": cleaned(output.strip(), root)}
    files = {PurePosixPath(name).name: name for name in sources}
    entries = [java_entry(id, name, cases.get(id), files) for id, name in named.items()]
    return {"tests": entries, "problem": None, "output": cleaned(output.strip(), root)}


def java_entry(id: str, name: str, case: Any, files: dict[str, str]) -> dict[str, Any]:
    """A Java test's result: a failure's message, with an assertEquals's expected and actual
    values, and an exception as an error with the deepest line of the session's own code, outside
    its tests, that it passed."""
    import re

    entry: dict[str, Any] = {
        "id": id,
        "name": name,
        "status": "pass",
        "message": None,
        "expected": None,
        "actual": None,
        "location": None,
        "output": "",
        "note": None,
        "durationMs": round(float(case.get("time", 0)) * 1000) if case is not None else 0,
    }
    if case is None:
        entry["status"] = "error"
        entry["message"] = "Didn't run."
        return entry
    failed = next(
        (each for each in (case.find("failure"), case.find("error")) if each is not None), None
    )
    if case.find("skipped") is not None:
        entry["status"] = "skip"
    elif failed is not None:
        message = failed.get("message") or failed.get("type") or "The check failed."
        compared = re.search(r"expected: <(.*)> but was: <(.*)>$", message, re.DOTALL)
        if compared:
            entry["expected"], entry["actual"] = compared[1], compared[2]
        if failed.get("type", "").startswith(("org.opentest4j.", "org.junit.")):
            entry["status"] = "fail"
            entry["message"] = clip(message)
        else:
            entry["status"] = "error"
            entry["message"] = clip(f"{failed.get('type', '').rsplit('.', 1)[-1]}: {message}")
            for found in re.finditer(
                r"^\s*at [^(]+\(([^:()]+\.java):(\d+)\)", failed.text or "", re.MULTILINE
            ):
                if found[1] in files:
                    entry["location"] = {"file": files[found[1]], "line": int(found[2])}
                    break
    return entry


def java_build_problem(said: str, root: Path) -> dict[str, Any]:
    """javac's first error as the run's problem, with its file and line."""
    import re

    for line in said.splitlines():
        found = re.match(r"^(.+?\.java):(\d+): error: (.+)$", line.strip())
        if found:
            file = cleaned(found[1], root).replace(os.sep, "/")
            return {
                "kind": "BuildError",
                "message": clip(found[3]),
                "location": {"file": file, "line": int(found[2])},
            }
    said = said.strip() or "javac stopped without saying why."
    return {"kind": "BuildError", "message": clip(cleaned(said, root)), "location": None}


def cleaned(text: str, root: Path) -> str:
    """Paths and addresses shown from the session's folder, as the learner sees their files."""
    return text.replace(f"{root.as_uri()}/", "").replace(f"{root}{os.sep}", "")


def prepare(files_json: str, packages_json: str) -> None:
    """Import the modules that the session's Python files import from these packages, and with
    mypy among them, check the session's files with it once. Then freeze what's alive out of
    garbage collection.

    The first import of a module such as scipy.stats can take seconds in a browser, as can
    mypy's first check, and the browser times a run from after this, so a run's time goes on
    the session's own code. Only the packages' modules are imported, never the session's files.
    What the packages load stays alive for as long as Python runs, as do the types mypy reads,
    and every full collection in a run would go through it all again: frozen, it's left out,
    and the session's own objects are collected as before.
    """
    files: dict[str, str] = json.loads(files_json)
    packages = set(json.loads(packages_json))
    for name in imported(files):
        if name.split(".")[0] in packages:
            # A module that isn't there fails again in the run, which reports it.
            with suppress(Exception):
                importlib.import_module(name)
    if "mypy" in packages:
        # A problem here shows again in the run, which reports it.
        with suppress(Exception):
            warm(files)
    gc.collect()
    gc.freeze()


def warm(files: dict[str, str]) -> None:
    """Check the session's own Python files with mypy, in a folder of their own, so that the
    types of what they import are in mypy's cache before a run's time starts. mypy's first check
    reads the standard library's types, which takes seconds in a browser.

    mypy keeps a file's errors in its cache with the path it was given, and gives them again
    while the file is unchanged, so the files are checked from their folder by name, as a test
    checks them."""
    sources = [name for name in files if name.endswith(".py") and not name.startswith("tests/")]
    with session_folder() as folder, chdir(folder):
        write(Path(folder), {name: files[name] for name in sources})
        check_types(*sources)


def imported(files: dict[str, str]) -> list[str]:
    """Every module the Python files import, first to last. A name a from-import takes may be
    a module too, as in `from scipy import stats`, so it is listed under the module's name."""
    found: dict[str, None] = {}
    for name, text in files.items():
        if not name.endswith(".py"):
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(dict.fromkeys(alias.name for alias in node.names))
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found[node.module] = None
                found.update(dict.fromkeys(f"{node.module}.{alias.name}" for alias in node.names))
    return list(found)


def figures(files_json: str, links_json: str = "{}") -> str:
    """Call figures() in the session's figures.py, and return the numbers it gives or its error.

    A stage's prose shows numbers from its figures.py rather than typing them, so every number a
    learner reads is computed, the same way in the browser's Python and in CPython.
    """
    files: dict[str, str] = json.loads(files_json)
    with session_folder() as folder:
        root = Path(folder).resolve()
        write(root, files)
        link(root, json.loads(links_json))
        try:
            values = within(root, lambda: importlib.import_module("figures").figures())
        except Exception as error:
            return json.dumps({"figures": None, "problem": f"{type(error).__name__}: {error}"})
    named = isinstance(values, dict) and all(
        isinstance(name, str) and isinstance(value, str) for name, value in values.items()
    )
    if not named:
        return json.dumps({"figures": None, "problem": "figures() must return names and strings."})
    return json.dumps({"figures": values, "problem": None})


def chart(files_json: str, values_json: str) -> str:
    """Call chart() in the session's chart.py with the sliders' values, and return what it draws
    or its error.

    A chart draws the learner's own functions: chart.py imports them from the session's files,
    and each slider's value arrives as a keyword argument.
    """
    files: dict[str, str] = json.loads(files_json)
    values: dict[str, float] = json.loads(values_json)
    with session_folder() as folder:
        root = Path(folder).resolve()
        write(root, files)
        try:
            drawing = within(root, lambda: plain(importlib.import_module("chart").chart(**values)))
            return json.dumps({"chart": drawing, "problem": None}, allow_nan=False)
        # A learner's sys.exit() is an error in their code, not a reason to stop the runner.
        except (Exception, SystemExit) as error:
            message = clip(str(error).replace(f"{root}{os.sep}", ""))
            return json.dumps(
                {"chart": None, "problem": {"kind": type(error).__name__, "message": message}}
            )


def plain(value: object) -> object:
    """value as JSON holds it: NumPy arrays and numbers become lists and Python numbers, and a
    number that isn't finite becomes None, since JSON can't write it."""
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def session_folder() -> tempfile.TemporaryDirectory[str]:
    """A new folder for a session. Windows can't delete a file that is open, so a file the
    session's code leaves open stays behind in it rather than stopping the run."""
    return tempfile.TemporaryDirectory(prefix="sulba-", ignore_cleanup_errors=True)


def write(root: Path, files: dict[str, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        path = root / safe(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")


def link(root: Path, links: dict[str, str]) -> None:
    """Put each file on disk at its path in the session: a hard link to it where the system
    allows one, and a copy where it doesn't. A machine lab's fetched files, such as a dataset or
    a model's weights, are too large to send as text (decision record 29)."""
    for name, source in links.items():
        path = root / safe(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(source, path)
        except OSError:
            shutil.copyfile(source, path)


def arguments(tests: list[str], config: Path) -> list[str]:
    return [
        *tests,
        "-q",
        "--tb=no",
        "-p",
        "no:cacheprovider",
        "-c",
        str(config),
        "--rootdir",
        ".",
        # Print output is kept per test. Pyodide has no file descriptors to capture.
        "--capture=sys",
        # Test files are imported without changing sys.path, so the session's own modules are
        # found only in its folder.
        "--import-mode=importlib",
        "-W",
        "ignore",
    ]


def safe(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"A session file must sit inside the session: {name}")
    return path


def within(root: Path, action: Any) -> Any:
    """Run action from root, with root importable, then forget every module it loaded.

    pytest's own report is discarded: results come from the plugin. Its terminal plugin stays
    loaded, because pytest writes a failed assertion's explanation through it.
    """
    cwd = os.getcwd()
    path = sys.path[:]
    bytecode = sys.dont_write_bytecode
    os.chdir(root)
    sys.path.insert(0, str(root))
    sys.dont_write_bytecode = True
    importlib.invalidate_caches()
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return action()
    finally:
        os.chdir(cwd)
        sys.path[:] = path
        sys.dont_write_bytecode = bytecode
        for name, module in list(sys.modules.items()):
            file = getattr(module, "__file__", None)
            if file and Path(file).resolve().is_relative_to(root):
                del sys.modules[name]


def shown(value: object) -> str:
    text = repr(value)
    return text if len(text) <= LIMIT else f"{text[: LIMIT - 1]}…"


class Report:
    """A pytest plugin that keeps what a learner needs from each test."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.tests: dict[str, dict[str, Any]] = {}
        self.problem: dict[str, Any] | None = None
        self.output = ""
        self.compared: dict[str, tuple[str, str]] = {}
        self.current: str | None = None

    def pytest_configure(self, config: pytest.Config) -> None:
        config.addinivalue_line("markers", "id(value): the test's permanent id")

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_call(self, item: pytest.Item) -> Any:
        self.current = item.nodeid
        try:
            return (yield)
        finally:
            self.current = None

    # Tests are written `assert actual == expected`, so a failed comparison gives both sides.
    def pytest_assertrepr_compare(self, op: str, left: object, right: object) -> None:
        if self.current is not None and self.current not in self.compared:
            self.compared[self.current] = (shown(left), shown(right))

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Item, call: pytest.CallInfo[None]) -> Any:
        report: pytest.TestReport = yield
        entry = self.tests.setdefault(item.nodeid, self.entry(item))
        entry["durationMs"] += round(report.duration * 1000)
        # Each phase's report repeats the output of the phases before it.
        entry["output"] = report.capstdout + report.capstderr
        for name, value in report.user_properties:
            if name == "note":
                entry["note"] = clip(str(value))
        if report.failed and entry["status"] == "pass":
            excinfo = call.excinfo
            failed = excinfo is not None and excinfo.errisinstance(AssertionError)
            entry["status"] = "fail" if failed else "error"
            if excinfo is not None:
                entry["message"] = self.message(excinfo.value, failed)
                entry["location"] = self.location(excinfo)
            entry["actual"], entry["expected"] = self.compared.get(item.nodeid, (None, None))
        return report

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        self.output += report.capstdout + report.capstderr

    def pytest_exception_interact(
        self, node: pytest.Item | pytest.Collector, call: pytest.CallInfo[Any], report: Any
    ) -> None:
        if isinstance(node, pytest.Collector) and self.problem is None and call.excinfo:
            error = call.excinfo.value
            # pytest wraps an error raised while importing a test file. The learner needs the
            # error underneath, such as a syntax error in their own file.
            if isinstance(error, pytest.Collector.CollectError) and error.__cause__:
                error = error.__cause__
            self.problem = {
                "kind": type(error).__name__,
                "message": self.problem_message(error),
                "location": self.location(pytest.ExceptionInfo.from_exception(error)),
            }

    def entry(self, item: pytest.Item) -> dict[str, Any]:
        marker = item.get_closest_marker("id")
        doc = getattr(getattr(item, "function", None), "__doc__", None)
        return {
            "id": str(marker.args[0]) if marker and marker.args else None,
            "name": doc.strip().splitlines()[0] if doc and doc.strip() else item.name,
            "status": "pass",
            "message": None,
            "expected": None,
            "actual": None,
            "location": None,
            "output": "",
            "note": None,
            "durationMs": 0,
        }

    def location(self, excinfo: pytest.ExceptionInfo[BaseException]) -> dict[str, Any] | None:
        """The deepest line of the session's own code, outside its tests, that the error passed."""
        error = excinfo.value
        if isinstance(error, SyntaxError) and error.filename and error.lineno:
            found = self.relative(error.filename)
            if found:
                return {"file": found, "line": error.lineno}
        place = None
        for entry in excinfo.traceback:
            found = self.relative(str(entry.path))
            if found and not found.startswith("tests/"):
                place = {"file": found, "line": entry.lineno + 1}
        return place

    def relative(self, file: str) -> str | None:
        path = Path(file).resolve()
        return path.relative_to(self.root).as_posix() if path.is_relative_to(self.root) else None

    def result(self, exit_code: int) -> dict[str, Any]:
        problem = self.problem
        # 0: every test passed. 1: some failed. 2: collection failed, which set the problem.
        if problem is None and exit_code not in (0, 1):
            ran = "No tests ran." if exit_code == 5 else f"pytest stopped with code {exit_code}."
            problem = {"kind": "RunError", "message": ran, "location": None}
        return {
            "tests": [] if problem else list(self.tests.values()),
            "problem": problem,
            "output": self.output,
        }

    def message(self, error: BaseException, failed: bool) -> str:
        """The first line of an assertion's message, or the error's type and any message."""
        if failed:
            lines = str(error).strip().splitlines()
            return self.clean(lines[0] if lines else "The check failed.")
        said = str(error)
        return self.clean(f"{type(error).__name__}: {said}" if said else type(error).__name__)

    def problem_message(self, error: BaseException) -> str:
        return self.clean(error.msg if isinstance(error, SyntaxError) else str(error))

    def clean(self, text: str) -> str:
        """Paths shown from the session's folder, as the learner sees their files."""
        return clip(text.replace(f"{self.root}{os.sep}", ""))


def clip(text: str) -> str:
    return text if len(text) <= LIMIT else f"{text[: LIMIT - 1]}…"


if __name__ == "__main__":
    # One request per line of standard input and its answer on one line of standard output, so
    # checks can run many sessions in one process. A run is {"files": {...}, "tests": [...]},
    # {"files": {...}, "figures": true} asks for figures.py's numbers, and
    # {"files": {...}, "chart": {...}} for what chart.py draws with those values. A run or a
    # figures request may add {"links": {...}}: files on disk, by their path in the session.
    # Requests come in UTF-8, which Windows doesn't read a pipe in by default.
    sys.stdin.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        request = json.loads(line)
        files = json.dumps(request["files"])
        links = json.dumps(request.get("links", {}))
        if request.get("figures"):
            print(figures(files, links), flush=True)
        elif "chart" in request:
            print(chart(files, json.dumps(request["chart"])), flush=True)
        else:
            print(run(files, json.dumps(request["tests"]), links), flush=True)

"""Spike: does Go 1.27.3 from go.dev run a package's tests through go test -json on this runner,
with subtests named for their ids, a fake clock from testing/synctest, an httptest server, a
benchmark and a build failure, using nothing but the archive? Stdlib only. It runs the package
from a copy in a folder whose name has non-ASCII letters."""

import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile
from pathlib import Path

VERSION = "1.27.3"
# From https://go.dev/dl/?mode=json.
BUILDS = {
    ("Linux", "x86_64"): ("linux-amd64.tar.gz", "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40"),
    ("Linux", "aarch64"): ("linux-arm64.tar.gz", "a06e99309dbcbdca1a8ccd2282c3ee146e55930886e26b4f1193269587165f49"),
    ("Darwin", "arm64"): ("darwin-arm64.tar.gz", "dd3908cf20959d798c1e06ebe5b72213f0505ce01373b40ce3110975a6cd99c2"),
    ("Darwin", "x86_64"): ("darwin-amd64.tar.gz", "b6f8e931e4ab497fcde6da8ae4499a58f9d258e55c8a80824a516eae5950a750"),
    ("Windows", "AMD64"): ("windows-amd64.zip", "f26081f438319757f8a1b46d7d0b2c5ec7583d4038e485e0aa725cfde7885fff"),
    ("Windows", "ARM64"): ("windows-arm64.zip", "c507872ff21f8a7cd3c1c217b059c6f7271a4a9d8e692810ef9dd3e1f601197c"),
}
HERE = Path(__file__).parent


def timed(label, command, cwd, env):
    start = time.monotonic()
    done = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8")
    seconds = time.monotonic() - start
    print(f"== {label}: exit {done.returncode} in {seconds:.1f} s")
    print(done.stdout[-6000:])
    print(done.stderr[-3000:], file=sys.stderr)
    return done


def events(done):
    return [json.loads(line) for line in done.stdout.splitlines() if line.startswith("{")]


def main():
    key = (platform.system(), platform.machine())
    print("system", key, platform.platform())
    suffix, sha256 = BUILDS[key]
    name = f"go{VERSION}.{suffix}"
    start = time.monotonic()
    with urllib.request.urlopen(f"https://go.dev/dl/{name}") as response:
        archive = response.read()
    print(f"== download {name}: {len(archive)} bytes in {time.monotonic() - start:.1f} s")
    assert hashlib.sha256(archive).hexdigest() == sha256, "sha256 differs"
    home = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "spike-go"
    shutil.rmtree(home, ignore_errors=True)
    home.mkdir(parents=True)
    start = time.monotonic()
    if suffix.endswith(".zip"):
        zipfile.ZipFile(io.BytesIO(archive)).extractall(home)
    else:
        tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz").extractall(home, filter="tar")
    print(f"== extract: {time.monotonic() - start:.1f} s")
    go = home / "go" / "bin" / ("go.exe" if key[0] == "Windows" else "go")
    project = home / "Dossier de données é"
    shutil.copytree(HERE, project, ignore=shutil.ignore_patterns("run.py"))
    cache = home / "cache"
    env = os.environ | {
        "GOTOOLCHAIN": "local",
        "GOENV": "off",
        "GOFLAGS": "-mod=readonly",
        "CGO_ENABLED": "0",
        "GOPATH": str(cache / "path"),
        "GOCACHE": str(cache / "build"),
        "GOMODCACHE": str(cache / "mod"),
    }
    results = {}
    results["version"] = timed("go version", [str(go), "version"], project, env).stdout.strip()
    results["telemetry"] = timed("go telemetry", [str(go), "telemetry"], project, env).stdout.strip()
    first = timed("go test, first", [str(go), "test", "-json", "-count=1", "."], project, env)
    again = timed("go test, again", [str(go), "test", "-json", "-count=1", "."], project, env)
    tests = {}
    for event in events(again):
        if event.get("Test") and event["Action"] in ("pass", "fail", "skip"):
            tests[event["Test"]] = event["Action"]
    results["tests"] = tests
    results["failure output"] = "".join(
        event["Output"]
        for event in events(again)
        if event.get("Test", "").startswith("TestLimiter/tst_bbbbbb") and event["Action"] == "output"
    )
    results["first exit"] = first.returncode
    bad = timed("go test bad", [str(go), "test", "-json", "-count=1", "./bad"], project, env)
    results["bad"] = [
        (event["Action"], event.get("Output", "").strip())
        for event in events(bad)
        if event["Action"].startswith("build")
    ]
    results["vet"] = timed("go vet", [str(go), "vet", "."], project, env).returncode
    bench = timed(
        "go test -bench",
        [str(go), "test", "-run", "^$", "-bench", ".", "-benchtime", "1000x", "."],
        project,
        env,
    )
    results["bench"] = bench.returncode, "BenchmarkLimiter" in bench.stdout
    print("RESULTS", json.dumps(results, ensure_ascii=False, indent=1))
    expected_tests = {
        "TestLimiter/tst_aaaaaa_waits_a_tenth_of_a_second_for_its_second_token": "pass",
        "TestLimiter/tst_bbbbbb_a_failing_one": "fail",
        "TestLimiter/tst_dddddd_gives_up_when_its_context_ends": "pass",
        "TestLimiter": "fail",
        "TestProxy/tst_cccccc_passes_the_request_on": "pass",
        "TestProxy": "pass",
    }
    ok = (
        results["version"].startswith(f"go version go{VERSION} ")
        and results["tests"] == expected_tests
        and "gateway_test.go:" in results["failure output"]
        and "got 1, want 2" in results["failure output"]
        and any(action == "build-fail" for action, _ in results["bad"])
        and any("cannot use" in output for _, output in results["bad"])
        and results["vet"] == 0
        and results["bench"] == (0, True)
    )
    print("OK" if ok else "NOT OK")
    sys.exit(0 if ok else 1)


main()

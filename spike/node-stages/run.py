"""Spike: does Node 24.22.1 from nodejs.org, with typescript 7.0.2 and happy-dom 21.0.4 from npm,
run a typed DOM test through node --test and type-check it with tsc, on this runner? Stdlib only.
It runs the project from a copy in a folder whose name has non-ASCII letters."""

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

VERSION = "24.22.1"
# From https://nodejs.org/dist/v24.22.1/SHASUMS256.txt.
BUILDS = {
    ("Linux", "x86_64"): ("linux-x64.tar.xz", "6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6"),
    ("Linux", "aarch64"): ("linux-arm64.tar.xz", "dbabf7a1cbf947e6059ffad2c27b80041db97dea1e553b62afdee7f13fca336e"),
    ("Darwin", "arm64"): ("darwin-arm64.tar.gz", "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7"),
    ("Darwin", "x86_64"): ("darwin-x64.tar.gz", "d132557e7ee2b85af08b0c8c34338e65c6430f2238d01f727728ef42dc83b035"),
    ("Windows", "AMD64"): ("win-x64.zip", "d2046d28c2c3dcd211ac5145c0bf30e2047ef9dfb306693c8c6e2eccd8b95fa5"),
    ("Windows", "ARM64"): ("win-arm64.zip", "a0c807319fede24c4a0d8f84564c82a619bd313b16b10c007c383c2609e99171"),
}
HERE = Path(__file__).parent


def timed(label, command, cwd, **kwargs):
    start = time.monotonic()
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", **kwargs)
    seconds = time.monotonic() - start
    print(f"== {label}: exit {done.returncode} in {seconds:.1f} s")
    print(done.stdout[-4000:])
    print(done.stderr[-2000:], file=sys.stderr)
    return done


def main():
    key = (platform.system(), platform.machine())
    print("system", key, platform.platform())
    suffix, sha256 = BUILDS[key]
    name = f"node-v{VERSION}-{suffix}"
    start = time.monotonic()
    with urllib.request.urlopen(f"https://nodejs.org/dist/v{VERSION}/{name}") as response:
        archive = response.read()
    print(f"== download {name}: {len(archive)} bytes in {time.monotonic() - start:.1f} s")
    assert hashlib.sha256(archive).hexdigest() == sha256, "sha256 differs"
    home = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "spike-node"
    shutil.rmtree(home, ignore_errors=True)
    home.mkdir(parents=True)
    if suffix.endswith(".zip"):
        zipfile.ZipFile(io.BytesIO(archive)).extractall(home)
        root = home / name.removesuffix(".zip")
        node = root / "node.exe"
    else:
        mode = "r:xz" if suffix.endswith(".xz") else "r:gz"
        tarfile.open(fileobj=io.BytesIO(archive), mode=mode).extractall(home, filter="tar")
        root = home / name.split(".tar")[0]
        node = root / "bin" / "node"
    npm = next(root.rglob("npm-cli.js"))
    print("node", node, "npm", npm)
    project = home / "Dossier de données é"
    shutil.copytree(HERE, project, ignore=shutil.ignore_patterns("run.py", "node_modules"))
    env = os.environ | {"npm_config_update_notifier": "false"}
    results = {}
    results["version"] = timed("node --version", [str(node), "--version"], project).stdout.strip()
    ci = timed("npm ci", [str(node), str(npm), "ci", "--no-audit", "--no-fund"], project, env=env)
    results["npm ci"] = ci.returncode
    test = timed(
        "node --test",
        [str(node), "--test", "--test-reporter=./reporter.mjs", "tests/messages.test.ts"],
        project,
    )
    events = [json.loads(line) for line in test.stdout.splitlines() if line.startswith("{")]
    results["tests"] = [(e["type"], e["name"], e.get("expected"), e.get("actual")) for e in events]
    tsc = project / "node_modules" / "typescript" / "bin" / "tsc"
    results["tsc"] = timed("tsc -p .", [str(node), str(tsc), "-p", "."], project).returncode
    bad = timed("tsc bad.ts", [str(node), str(tsc), "--ignoreConfig", "--noEmit", "--strict", "bad.ts"], project)
    results["tsc bad"] = (bad.returncode, "TS2322" in bad.stdout)
    print("RESULTS", json.dumps(results))
    expected_tests = [
        ["test:pass", "tst_aaaaaa Shows each message as text", None, None],
        ["test:fail", "tst_bbbbbb A failing one", {"a": 2}, {"a": 1}],
    ]
    ok = (
        results["version"] == f"v{VERSION}"
        and results["npm ci"] == 0
        and json.loads(json.dumps(results["tests"])) == expected_tests
        and results["tsc"] == 0
        and results["tsc bad"][0] != 0
        and results["tsc bad"][1]
    )
    print("OK" if ok else "NOT OK")
    sys.exit(0 if ok else 1)


main()

"""Spike: on this runner, does PySpark 4.2.0 run its cases on a Temurin 21 JRE fetched by sha256,
and does Sail 0.7.2 with pyspark-client run them, how long does each take, and what does each give?
Stdlib only; each engine's results print as one RESULT line of JSON."""

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

RELEASE = "jdk-21.0.12.1%2B1"
# From Adoptium's API for the release, each JRE's file and sha256.
JRES = {
    ("Windows", "AMD64"): ("OpenJDK21U-jre_x64_windows_hotspot_21.0.12.1_1.zip", "d35f31e712f0fcf6ac5a093edc90204fbff22f720ba3950bd09d331d5e621636"),
    ("Windows", "ARM64"): ("OpenJDK21U-jre_aarch64_windows_hotspot_21.0.12.1_1.zip", "e82cc17e0bf89a25b0b0ed106d072f2ea420587d0a6870534b71b1dce3ae28c3"),
    ("Darwin", "x86_64"): ("OpenJDK21U-jre_x64_mac_hotspot_21.0.12.1_1.tar.gz", "6717ec641fd9ce0bb209ca083ee23b42202ac68cb6fcc5753496e0e4a0f41989"),
    ("Darwin", "arm64"): ("OpenJDK21U-jre_aarch64_mac_hotspot_21.0.12.1_1.tar.gz", "dec50fc6f9fcd4fe3ae8cabf5a5fa68f6afc48841f7698e468e9aa5d54beed84"),
    ("Linux", "x86_64"): ("OpenJDK21U-jre_x64_linux_hotspot_21.0.12.1_1.tar.gz", "2413149700df0f7d440500a84a8f764c535f21e5a5e87d38328b64eec2c5b500"),
    ("Linux", "aarch64"): ("OpenJDK21U-jre_aarch64_linux_hotspot_21.0.12.1_1.tar.gz", "14be1f35ebdbd1f6e8d57eb911a3ffb74d6d9aa255abc5daf2b1302002cf2cf2"),
}
HERE = Path(__file__).parent


def timed(label, command, **kwargs):
    start = time.monotonic()
    done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", **kwargs)
    seconds = time.monotonic() - start
    print(f"== {label}: exit {done.returncode} in {seconds:.1f} s")
    print(done.stdout[-3000:])
    print(done.stderr[-3000:])
    return done, seconds


def jre(home):
    key = (platform.system(), platform.machine())
    name, sha256 = JRES[key]
    start = time.monotonic()
    url = f"https://github.com/adoptium/temurin21-binaries/releases/download/{RELEASE}/{name}"
    with urllib.request.urlopen(url) as response:
        archive = response.read()
    print(f"== JRE {name}: {len(archive)} bytes in {time.monotonic() - start:.1f} s")
    assert hashlib.sha256(archive).hexdigest() == sha256, "sha256 differs"
    if name.endswith(".zip"):
        zipfile.ZipFile(io.BytesIO(archive)).extractall(home)
    else:
        tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz").extractall(home, filter="data")
    [root] = [path for path in home.iterdir() if path.is_dir()]
    return root / "Contents" / "Home" if (root / "Contents" / "Home").is_dir() else root


def main():
    print("system", platform.system(), platform.machine(), platform.platform())
    work = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "spike-spark"
    shutil.rmtree(work, ignore_errors=True)
    (work / "jre").mkdir(parents=True)
    java_home = jre(work / "jre")
    print("JAVA_HOME", java_home)
    for engine, project in (("classic", "classic"), ("sail", "sail")):
        env = dict(os.environ)
        if engine == "classic":
            env["JAVA_HOME"] = str(java_home)
            env["PATH"] = str(java_home / "bin") + os.pathsep + env["PATH"]
        else:
            env["SPARK_HOME"] = str(work)
        synced, sync_seconds = timed(f"{engine} sync", ["uv", "sync", "--project", str(HERE / project)], env=env)
        summary = {"engine": engine, "system": f"{platform.system()} {platform.machine()}", "sync_s": round(sync_seconds, 1)}
        if synced.returncode != 0:
            summary["sync_error"] = (synced.stderr or synced.stdout)[-600:]
            print("RESULT " + json.dumps(summary))
            continue
        out = work / f"{engine}.json"
        ran, run_seconds = timed(
            f"{engine} cases",
            ["uv", "run", "--project", str(HERE / project), "python", str(HERE / "compare.py"), engine, str(out), str(work / engine)],
            env=env,
            timeout=900,
        )
        summary["run_s"] = round(run_seconds, 1)
        summary["exit"] = ran.returncode
        if out.exists():
            summary["results"] = json.loads(out.read_text(encoding="utf-8"))
        print("RESULT " + json.dumps(summary))


main()

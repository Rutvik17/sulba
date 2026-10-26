"""Spike: does Liberica's Lite JDK 25.0.5 compile a project with javac and run its JUnit 6 tests
through the console launcher on this runner, with tests in a package of their own, ids in display
names, Jackson 3 for JSON, an HTTP server on virtual threads, a fake clock, an exception in the code
under test and a compile error, using nothing but the archive and four jars? Stdlib only. It runs
the project from a copy in a folder whose name has non-ASCII letters."""

import hashlib
import io
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import xml.etree.ElementTree as ElementTree
import zipfile
from pathlib import Path

RELEASE = "https://github.com/bell-sw/Liberica/releases/download/25.0.5.0.2+5/bellsoft-jdk25.0.5.0.2+5-"
# Hashed from each archive; sizes from api.bell-sw.com.
JDKS = {
    ("Linux", "x86_64"): ("linux-amd64-lite.tar.gz", 83098331, "1017bff21d11331f652cc219403b43b63c139f040a32cea1770139fbfb474aeb"),
    ("Linux", "aarch64"): ("linux-aarch64-lite.tar.gz", 82325521, "d9e6bec48560f986848efd5c4a4540130291dd9c67ea9e2df0de5964426dda20"),
    ("Darwin", "x86_64"): ("macos-amd64-lite.tar.gz", 81646190, "0b461ac569ccfd733727b8ddafa78835bedbfa3ccfc9fba2fb2e47cf2ec6da82"),
    ("Darwin", "arm64"): ("macos-aarch64-lite.tar.gz", 80507572, "63a6b768183133d2acc87dcf5f4142185baa1aadf6b5d68267d840d7c694b729"),
    ("Windows", "AMD64"): ("windows-amd64-lite.zip", 82885946, "35218d3407607b170eeb6e8b048b46aac4e287d64b0d23691b5c5d5b3b8c7ea2"),
    ("Windows", "ARM64"): ("windows-aarch64-lite.zip", 80303853, "9fad7d8935ccb22de5a5c0b182a71bea53ab5eeb40ff42775badc99a31d66de4"),
}
MAVEN = "https://repo1.maven.org/maven2/"
JARS = {
    "junit": ("org/junit/platform/junit-platform-console-standalone/6.1.3/junit-platform-console-standalone-6.1.3.jar", "e62b96ac475dbcde8599ea905d088f65d90778f86e259b856a49fa5c4ea256ec"),
    "databind": ("tools/jackson/core/jackson-databind/3.2.4/jackson-databind-3.2.4.jar", "c4af37223d5024f1294a5450598b01b65f30c53d9e906f02c3955ba1fb14a67d"),
    "core": ("tools/jackson/core/jackson-core/3.2.4/jackson-core-3.2.4.jar", "494b9f5fccf008042d5a72c5bf00629b144c0ba7362a9864cbb02234c9772651"),
    "annotations": ("com/fasterxml/jackson/core/jackson-annotations/2.22/jackson-annotations-2.22.jar", "21ddb598807d3a51a876704eb979d9296e1c6a6f47ab1826ff88c6d6a127a2d0"),
}
HERE = Path(__file__).parent


def fetch(url, sha256):
    start = time.monotonic()
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read()
            break
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 4:
                raise
            time.sleep(2**attempt)
    print(f"== download {url.rsplit('/', 1)[1]}: {len(data)} bytes in {time.monotonic() - start:.1f} s")
    assert hashlib.sha256(data).hexdigest() == sha256, f"sha256 of {url} differs"
    return data


def timed(label, command, cwd):
    env = {key: value for key, value in os.environ.items() if key not in ("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "CLASSPATH")}
    start = time.monotonic()
    done = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"== {label}: exit {done.returncode} in {time.monotonic() - start:.1f} s")
    print(done.stdout[-4000:])
    print(done.stderr[-3000:], file=sys.stderr)
    return done


def main():
    key = (platform.system(), platform.machine())
    print("system", key, platform.platform())
    suffix, size, sha256 = JDKS[key]
    archive = fetch(RELEASE + suffix, sha256)
    assert len(archive) == size, "size differs"
    home = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "spike-java"
    shutil.rmtree(home, ignore_errors=True)
    home.mkdir(parents=True)
    start = time.monotonic()
    if suffix.endswith(".zip"):
        zipfile.ZipFile(io.BytesIO(archive)).extractall(home / "jdk")
    else:
        tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz").extractall(home / "jdk", filter="tar")
    print(f"== extract: {time.monotonic() - start:.1f} s")
    exe = ".exe" if key[0] == "Windows" else ""
    javac = next((home / "jdk").rglob("bin/javac" + exe))
    java = javac.with_name("java" + exe)
    print("javac at", javac.relative_to(home))
    if key[0] != "Windows":
        assert os.access(javac, os.X_OK), "javac isn't executable"
    jars = {}
    for name, (path, digest) in JARS.items():
        jars[name] = home / Path(path).name
        jars[name].write_bytes(fetch(MAVEN + path, digest))
    libraries = os.pathsep.join(str(jars[name]) for name in ("databind", "core", "annotations"))
    project = home / "Dossier de données é"
    shutil.copytree(HERE, project, ignore=shutil.ignore_patterns("run.py"))
    results = {}
    version = timed("java -version", [str(java), "-version"], project)
    results["version"] = "25.0.5" in version.stderr
    main_build = timed("javac main", [str(javac), "-encoding", "UTF-8", "--release", "25", "-Xlint:all", "-d", "out/main", "-cp", libraries, *map(str, Path(project, "src/gateway").glob("*.java"))], project)
    results["main compiles"] = main_build.returncode == 0
    tests_build = timed("javac tests", [str(javac), "-encoding", "UTF-8", "--release", "25", "-d", "out/tests", "-cp", os.pathsep.join(["out/main", libraries, str(jars["junit"])]), *map(str, Path(project, "tests").glob("*.java"))], project)
    results["tests compile"] = tests_build.returncode == 0
    run = timed("junit", [str(java), "-Dfile.encoding=UTF-8", "-jar", str(jars["junit"]), "execute", "--class-path", os.pathsep.join(["out/main", "out/tests", libraries]), "--select-package", "tests", "--reports-dir", "reports", "--details=none", "--disable-banner", "--disable-ansi-colors"], project)
    report = ElementTree.parse(project / "reports" / "TEST-junit-jupiter.xml")
    outcomes = {}
    for case in report.iter("testcase"):
        name = re.search(r"display-name: .* > (tst_\w+)", case.findtext("system-out") or "").group(1)
        failed = case.find("failure") if case.find("failure") is not None else case.find("error")
        outcomes[name] = "pass" if failed is None else (failed.tag, failed.get("message"), next((line.strip() for line in (failed.text or "").splitlines() if "gateway." in line), None))
    print("outcomes", outcomes)
    results["ids and outcomes"] = (
        outcomes.get("tst_aaaaaa") == "pass"
        and outcomes.get("tst_bbbbbb") == "pass"
        and outcomes.get("tst_eeeeee") == "pass"
        and outcomes.get("tst_cccccc", ("",))[0] == "failure"
        and "expected: <3> but was: <2>" in outcomes.get("tst_cccccc", ("", ""))[1]
    )
    results["exception's line"] = outcomes.get("tst_dddddd", ("", "", ""))[2] == "at gateway.Server.first(Server.java:34)"
    results["exit 1 on a failure"] = run.returncode == 1
    bad = timed("javac bad", [str(javac), "-encoding", "UTF-8", "-d", "out/bad", "bad/Bad.java"], project)
    first = next((line for line in bad.stderr.splitlines() if ": error: " in line), "")
    print("first error:", first)
    results["compile error"] = bad.returncode != 0 and first.replace("\\", "/").endswith("bad/Bad.java:5: error: incompatible types: int cannot be converted to String")
    print("results", results)
    sys.exit(0 if all(results.values()) else 1)


main()

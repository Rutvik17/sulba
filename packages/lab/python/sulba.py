"""Runs a lab's stages on your machine, with the tests and checks its page runs in the browser.

    uv run sulba.py          run the tests of the stage you're on
    uv run sulba.py finish   finish a Catch stage's review
    uv run sulba.py next     start the next stage, once this one is done

When a stage is done, it gives you a link to the lab's page, which marks the stage done there.
Before the first run, it fetches into data/ any files the lab needs that are too large for the
download, such as a dataset, from their publishers.
"""

# A lab that runs on the learner's machine downloads with this file at its top and its stages in
# .sulba/lab.json (decision record 28). The link's fragment carries the stage's attempts as the
# attempts table takes them (decision record 18), so the page records them as its own; a fragment
# never reaches the server. It holds them as JSON compressed with DEFLATE, in base64url. The files
# a lab fetches are each pinned by its size and sha256 (decision record 29).

from __future__ import annotations

import argparse
import base64
import hashlib
import http.client
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
import webbrowser
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


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="uv run sulba.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", choices=["run", "finish", "next"], default="run")
    command = parser.parse_args(argv).command
    if not (RUNNER / "lab.json").is_file():
        print("Run this in the folder of a lab you downloaded: it has no .sulba/lab.json.")
        return 1
    lab = json.loads((RUNNER / "lab.json").read_text(encoding="utf-8"))
    progress = load_progress(lab)
    if command == "next":
        code = start_next(lab, progress)
    else:
        code = run_stage(lab, progress, finishing=command == "finish")
    (RUNNER / "progress.json").write_text(json.dumps(progress, indent=2), encoding="utf-8")
    return code


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
    import sulba_runner

    result = json.loads(
        sulba_runner.run(
            json.dumps(session_files(lab, index)),
            json.dumps(list(stage["tests"])),
            json.dumps(session_links(lab)),
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
    """A run's files: the lab's datasets and references, the learner's files up to this stage,
    and the stage's tests and checks. Of data/, only the lab's own datasets are read: it also
    holds the files the lab fetches, and whatever the learner puts there."""
    files: dict[str, str] = {}
    for name in lab["data"]:
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
    missing = [each for each in lab["fetch"] if not whole(HERE / "data" / each["file"], each)]
    if not missing:
        return True
    print("Fetching the lab's files into data:")
    for each in missing:
        host = urlsplit(each["url"]).hostname
        about = f"  {each['file']}, {size(each['bytes'])}, from {host}"
        print(about, end="", flush=True)
        try:
            fetch(each, HERE / "data" / each["file"], about)
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
    path.parent.mkdir(exist_ok=True)
    # A fetch stopped after all of its file had come has only to move it into place.
    if not whole(partial, file):
        kept = partial.is_file()
        receive(file, partial, about)
        if kept and not whole(partial, file):
            # What a fetch cut short kept may not be the start of this file, so it starts again.
            partial.unlink()
            receive(file, partial, about)
        if not whole(partial, file):
            partial.unlink()
            raise Mismatch(file["url"])
    os.replace(partial, path)


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

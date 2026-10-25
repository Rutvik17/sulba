import json
from pathlib import Path

import pytest


def instructions(text):
    """Each instruction in a Dockerfile as its keyword and its arguments, with lines a
    backslash continues joined and comments left out."""
    found = []
    pending = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or (not pending and not stripped):
            continue
        if stripped.endswith("\\"):
            pending += stripped[:-1] + " "
            continue
        keyword, _, arguments = (pending + stripped).partition(" ")
        found.append((keyword.upper(), arguments.strip()))
        pending = ""
    return found


def stages():
    """The Dockerfile's stages, each a list of its instructions from its FROM on."""
    found = []
    for keyword, arguments in instructions(Path("Dockerfile").read_text()):
        if keyword == "FROM":
            found.append([])
        if found:
            found[-1].append((keyword, arguments))
    return found


def last_stage():
    found = stages()
    assert found, "The Dockerfile has no FROM."
    return found[-1]


def image(arguments):
    """The image a FROM names, without its options or stage name."""
    words = [word for word in arguments.split() if not word.startswith("--")]
    return words[0]


@pytest.mark.id("tst_pt6qmj")
def test_compiles_the_page_in_a_stage_of_its_own():
    found = stages()
    named = {}
    for stage in found[:-1]:
        words = stage[0][1].split()
        if len(words) >= 3 and words[-2].upper() == "AS":
            named[words[-1]] = stage
    compiling = [
        name
        for name, stage in named.items()
        if image(stage[0][1]).startswith("node:")
        and any(keyword == "RUN" and "tsc" in arguments for keyword, arguments in stage)
    ]
    assert compiling, "No stage before the last runs tsc on a node image."
    last = last_stage()
    assert image(last[0][1]).startswith("python:")
    copied = [
        arguments
        for keyword, arguments in last
        if keyword == "COPY" and f"--from={compiling[0]}" in arguments
    ]
    assert copied, (
        "The last stage copies nothing from the stage that compiles the page."
    )
    assert all("static" in arguments for arguments in copied)


@pytest.mark.id("tst_ezs8q2")
def test_installs_the_packages_the_lock_pins_without_the_dev_group():
    for stage in stages():
        environment = " ".join(
            arguments for keyword, arguments in stage if keyword == "ENV"
        )
        for keyword, arguments in stage:
            if keyword == "RUN" and "uv sync" in arguments:
                assert "--locked" in arguments or "--frozen" in arguments
                assert "--no-dev" in arguments or "UV_NO_DEV=1" in environment
                return
    pytest.fail("No stage runs uv sync.")


@pytest.mark.id("tst_ea1d9p")
def test_runs_the_desk_as_a_user_without_root():
    users = [arguments for keyword, arguments in last_stage() if keyword == "USER"]
    assert users, "The last stage sets no USER, so the desk runs as root."
    assert users[-1].split(":")[0] not in {"root", "0"}


@pytest.mark.id("tst_enxye1")
def test_starts_main_py_in_exec_form():
    commands = [arguments for keyword, arguments in last_stage() if keyword == "CMD"]
    assert commands, "The last stage has no CMD."
    command = json.loads(commands[-1])
    assert isinstance(command, list)
    assert "main.py" in command


@pytest.mark.id("tst_itfltw")
def test_has_a_health_check_that_asks_for_health():
    checks = [
        arguments for keyword, arguments in last_stage() if keyword == "HEALTHCHECK"
    ]
    assert checks, "The last stage has no HEALTHCHECK."
    assert "/health" in checks[-1]
    assert "/ready" not in checks[-1]

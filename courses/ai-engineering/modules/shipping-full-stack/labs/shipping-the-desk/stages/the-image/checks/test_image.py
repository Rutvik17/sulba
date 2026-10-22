import re
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


SECRET = re.compile(r"secret|password|token|key|database_url", re.IGNORECASE)


def names(arguments):
    """The variables an ENV or ARG sets."""
    if "=" not in arguments.split()[0]:
        return [arguments.split()[0]]
    return [
        pair.split("=")[0]
        for pair in re.findall(r'[A-Za-z_][A-Za-z0-9_]*=(?:"[^"]*"|\S*)', arguments)
    ]


@pytest.mark.id("tst_y1jyas")
def test_pins_each_image_to_a_version():
    found = stages()
    stage_names = {
        stage[0][1].split()[-1] for stage in found if " AS " in stage[0][1].upper()
    }
    images = []
    for stage in found:
        for keyword, arguments in stage:
            words = [word for word in arguments.split() if not word.startswith("--")]
            if keyword == "FROM":
                images.append(words[0])
            for word in arguments.split():
                if keyword == "COPY" and word.startswith("--from="):
                    images.append(word.removeprefix("--from="))
    for each in images:
        if each in stage_names:
            continue
        assert re.search(
            r"(:[^:@/]*\d+\.\d+\.\d+[^:@/]*|@sha256:[0-9a-f]{64})$", each
        ), each


@pytest.mark.id("tst_kdelyk")
def test_puts_no_secret_in_the_image():
    for stage in stages():
        for keyword, arguments in stage:
            if keyword in {"ENV", "ARG"}:
                for name in names(arguments):
                    assert not SECRET.search(name), name


@pytest.mark.id("tst_g3l0g9")
def test_copies_files_by_name():
    for stage in stages():
        for keyword, arguments in stage:
            if keyword in {"COPY", "ADD"} and "--from=" not in arguments:
                sources = [
                    word for word in arguments.split() if not word.startswith("--")
                ][:-1]
                assert not {".", "./", "*"} & set(sources), arguments


@pytest.mark.id("tst_ahnjta")
def test_leaves_the_build_tools_out_of_the_last_stage():
    for keyword, arguments in last_stage():
        assert not (keyword == "COPY" and "astral-sh/uv" in arguments), arguments
        assert not (keyword == "RUN" and re.search(r"\b(uv|npm|pip)\b", arguments)), (
            arguments
        )

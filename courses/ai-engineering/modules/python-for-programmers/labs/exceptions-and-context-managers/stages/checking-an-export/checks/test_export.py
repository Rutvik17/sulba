import builtins
import io

import pytest

from errors import Number, Object, String, Struct, StructError, check_export

SAMPLE = Object({"id": String(), "radius": Number()})
DAY = [
    '{"id": "S1", "radius": 17.99}\n',
    '{"id": "S2", "radius": "x"}\n',
    '{"id": "S3", "radius": 13.54\n',
    '{"id": "S4", "radius": 11.42}\n',
    '{"id": "S5", "radius": 20.29, "note": "repeat"}\n',
    '{"id": "S6", "radius": 12.45}\n',
]


class Broken(Struct):
    """A struct with a bug: its test divides by zero."""

    def test(self, value):
        return 1 / 0


def export(folder, lines, name="2026-10-16.jsonl"):
    path = folder / name
    path.write_text("".join(lines), encoding="utf-8")
    return path


def tracked(monkeypatch):
    """Every file opened from now on, through open or a Path."""
    files = []
    real = io.open

    def opening(*args, **kwargs):
        file = real(*args, **kwargs)
        files.append(file)
        return file

    monkeypatch.setattr(builtins, "open", opening)
    monkeypatch.setattr(io, "open", opening)
    return files


@pytest.mark.id("tst_qvmfhh")
def test_closes(tmp_path, monkeypatch):
    """Closes the export whatever happens"""
    clean = export(tmp_path, [DAY[0], DAY[3]], "2026-10-15.jsonl")
    failing = export(tmp_path, DAY)
    files = tracked(monkeypatch)
    check_export(clean, SAMPLE)
    with pytest.raises(ExceptionGroup):
        check_export(failing, SAMPLE)
    with pytest.raises(ZeroDivisionError):
        check_export(clean, Broken())
    assert len(files) >= 3
    assert all(file.closed for file in files)


@pytest.mark.id("tst_8tr49h")
def test_other_errors(tmp_path):
    """Lets an error that isn't a line's go on, as it was"""
    with pytest.raises(ZeroDivisionError):
        check_export(export(tmp_path, DAY), Broken())


@pytest.mark.id("tst_tjcogp")
def test_every_line(tmp_path):
    """Reports every failing line, in order"""
    with pytest.raises(ExceptionGroup) as raised:
        check_export(export(tmp_path, DAY), SAMPLE)
    found = [
        (type(error), getattr(error, "__notes__", []))
        for error in raised.value.exceptions
    ]
    assert found == [
        (StructError, ["Line 2"]),
        (ValueError, []),
        (StructError, ["Line 5"]),
    ]

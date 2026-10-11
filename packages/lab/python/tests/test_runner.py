import json
import subprocess
import sys
from pathlib import Path

import pytest

from sulba_runner import run

FIXTURES = Path(__file__).parents[2] / "fixtures"


def session(case: str) -> tuple[dict[str, str], list[str]]:
    folder = FIXTURES / case
    files = {
        path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(folder.rglob("*"))
        if path.is_file() and path.name != "expected.json"
    }
    return files, [name for name in files if name.startswith("tests/")]


def without_times(result: dict) -> dict:
    result = {key: value for key, value in result.items() if key != "durationMs"}
    result["tests"] = [
        {key: value for key, value in test.items() if key != "durationMs"}
        for test in result["tests"]
    ]
    return result


@pytest.mark.parametrize("case", sorted(path.name for path in FIXTURES.iterdir()))
def test_each_fixture_gives_its_expected_result(case: str) -> None:
    files, tests = session(case)
    result = json.loads(run(json.dumps(files), json.dumps(tests)))
    expected = json.loads((FIXTURES / case / "expected.json").read_text(encoding="utf-8"))
    assert without_times(result) == expected


def test_a_second_run_uses_the_new_code() -> None:
    files, tests = session("fails")
    first = json.loads(run(json.dumps(files), json.dumps(tests)))
    files["stats.py"] = files["stats.py"].replace("return sum(values)", "return 2 * sum(values)")
    second = json.loads(run(json.dumps(files), json.dumps(tests)))
    assert [test["status"] for test in first["tests"]] == ["pass", "fail", "error"]
    assert [test["status"] for test in second["tests"]] == ["fail", "fail", "error"]


def test_files_outside_the_session_are_refused() -> None:
    with pytest.raises(ValueError, match="inside the session"):
        run(json.dumps({"../stats.py": ""}), json.dumps([]))


def test_batch_mode_answers_each_line_with_a_result() -> None:
    requests = []
    for case in ("passes", "syntax-error"):
        files, tests = session(case)
        requests.append(json.dumps({"files": files, "tests": tests}))
    done = subprocess.run(
        [sys.executable, "sulba_runner.py"],
        input="\n".join(requests) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=Path(__file__).parents[1],
        check=True,
    )
    results = [json.loads(line) for line in done.stdout.splitlines()]
    assert [len(result["tests"]) for result in results] == [2, 0]
    assert results[1]["problem"]["kind"] == "SyntaxError"

import gc
import json
import subprocess
import sys
import weakref
from collections.abc import Iterator
from pathlib import Path

import pytest

from sulba_runner import chart, figures, imported, prepare, run

FIXTURES = Path(__file__).parents[2] / "fixtures"


@pytest.fixture(autouse=True)
def unfrozen() -> Iterator[None]:
    """prepare freezes what's alive, which here is pytest's own objects too."""
    yield
    gc.unfreeze()


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


def test_imported_lists_each_module_the_python_files_import() -> None:
    files = {
        "model.py": (
            "import numpy as np, os\nfrom scipy import stats\n"
            "from scipy.stats import norm\nfrom . import local\n"
        ),
        "broken.py": "def f(:\n",
        "notes.txt": "import email\n",
    }
    assert imported(files) == ["numpy", "os", "scipy", "scipy.stats", "scipy.stats.norm"]


def test_prepare_imports_the_packages_modules_and_never_the_sessions_files() -> None:
    files = {
        "server.py": "from wsgiref import validate\nimport helpers\n",
        "helpers.py": "raise RuntimeError('a session file ran')\n",
    }
    assert "wsgiref.validate" not in sys.modules
    prepare(json.dumps(files), json.dumps(["wsgiref"]))
    assert "wsgiref.validate" in sys.modules
    assert "helpers" not in sys.modules


def test_prepare_freezes_what_is_alive_out_of_garbage_collection() -> None:
    assert gc.get_freeze_count() == 0
    prepare(json.dumps({}), json.dumps([]))
    assert gc.get_freeze_count() > 0


def test_prepare_collects_garbage_before_it_freezes() -> None:
    class Node:
        next: object

    gc.disable()
    try:
        node = Node()
        node.next = node
        gone = weakref.ref(node)
        del node
        prepare(json.dumps({}), json.dumps([]))
    finally:
        gc.enable()
    assert gone() is None


def test_files_outside_the_session_are_refused() -> None:
    with pytest.raises(ValueError, match="inside the session"):
        run(json.dumps({"../stats.py": ""}), json.dumps([]))


# A file on disk a run links into its session, as a machine lab's fetched files are: bytes, not
# text.
TILES = bytes(range(256)) * 4

TILES_TEST = '''import pytest


@pytest.mark.id("tst_aaaaaa")
def test_tiles():
    """Reads the linked tiles"""
    with open("data/tiles.bin", "rb") as file:
        assert len(file.read()) == 1024
'''


def test_a_run_has_each_linked_file_at_its_path(tmp_path: Path) -> None:
    source = tmp_path / "tiles.bin"
    source.write_bytes(TILES)
    files = {"tests/test_tiles.py": TILES_TEST}
    links = {"data/tiles.bin": str(source)}
    result = json.loads(run(json.dumps(files), json.dumps(list(files)), json.dumps(links)))
    assert [test["status"] for test in result["tests"]] == ["pass"]
    # The session goes when the run ends, and the file stays as it was.
    assert source.read_bytes() == TILES


def test_a_file_the_system_cannot_link_is_copied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unlinkable(source: str, path: Path) -> None:
        raise OSError("Hard links aren't supported here.")

    monkeypatch.setattr("os.link", unlinkable)
    source = tmp_path / "tiles.bin"
    source.write_bytes(TILES)
    files = {"tests/test_tiles.py": TILES_TEST}
    links = {"data/tiles.bin": str(source)}
    result = json.loads(run(json.dumps(files), json.dumps(list(files)), json.dumps(links)))
    assert [test["status"] for test in result["tests"]] == ["pass"]


def test_linked_files_outside_the_session_are_refused(tmp_path: Path) -> None:
    source = tmp_path / "tiles.bin"
    source.write_bytes(TILES)
    with pytest.raises(ValueError, match="inside the session"):
        run(json.dumps({}), json.dumps([]), json.dumps({"../tiles.bin": str(source)}))


def test_figures_have_each_linked_file_at_its_path(tmp_path: Path) -> None:
    source = tmp_path / "tiles.bin"
    source.write_bytes(TILES)
    files = {
        "figures.py": (
            "def figures():\n"
            "    with open('data/tiles.bin', 'rb') as file:\n"
            "        return {'bytes': str(len(file.read()))}\n"
        )
    }
    answer = json.loads(figures(json.dumps(files), json.dumps({"data/tiles.bin": str(source)})))
    assert answer == {"figures": {"bytes": "1024"}, "problem": None}


def test_batch_mode_links_each_requests_files(tmp_path: Path) -> None:
    source = tmp_path / "tiles.bin"
    source.write_bytes(TILES)
    files = {"tests/test_tiles.py": TILES_TEST}
    request = {"files": files, "tests": list(files), "links": {"data/tiles.bin": str(source)}}
    done = subprocess.run(
        [sys.executable, "sulba_runner.py"],
        input=json.dumps(request) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=Path(__file__).parents[1],
        check=True,
    )
    assert [test["status"] for test in json.loads(done.stdout)["tests"]] == ["pass"]


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


COUNTED = {
    "data/votes.csv": "choice\nyes\nno\nyes\n",
    "figures.py": (
        "import csv\n\n\n"
        "def figures():\n"
        "    with open('data/votes.csv', encoding='utf-8') as file:\n"
        "        votes = [row['choice'] for row in csv.DictReader(file)]\n"
        "    return {'yes': str(votes.count('yes')), 'share': f'{votes.count(\"yes\") / 3:.4f}'}\n"
    ),
}


def test_figures_are_the_strings_figures_py_returns() -> None:
    answer = json.loads(figures(json.dumps(COUNTED)))
    assert answer == {"figures": {"yes": "2", "share": "0.6667"}, "problem": None}


def test_figures_that_fail_give_the_error() -> None:
    files = {"figures.py": "def figures():\n    return {'x': str(1 / 0)}\n"}
    answer = json.loads(figures(json.dumps(files)))
    assert answer == {"figures": None, "problem": "ZeroDivisionError: division by zero"}


def test_figures_must_be_strings() -> None:
    files = {"figures.py": "def figures():\n    return {'x': 0.5}\n"}
    answer = json.loads(figures(json.dumps(files)))
    assert answer == {"figures": None, "problem": "figures() must return names and strings."}


def test_batch_mode_answers_a_figures_request() -> None:
    done = subprocess.run(
        [sys.executable, "sulba_runner.py"],
        input=json.dumps({"files": COUNTED, "figures": True}) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=Path(__file__).parents[1],
        check=True,
    )
    assert json.loads(done.stdout)["figures"] == {"yes": "2", "share": "0.6667"}


SHARES = {
    "data/votes.csv": "choice\nyes\nno\nyes\n",
    "tally.py": "def share(votes, choice):\n    return votes.count(choice) / len(votes)\n",
    "chart.py": (
        "import csv\n\n"
        "import numpy as np\n\n"
        "from tally import share\n\n\n"
        "def chart(votes):\n"
        "    with open('data/votes.csv', encoding='utf-8') as file:\n"
        "        cast = [row['choice'] for row in csv.DictReader(file)][:votes]\n"
        "    yes = share(cast, 'yes')\n"
        "    return {\n"
        "        'x': {'min': 0, 'max': 1, 'step': 1, 'label': 'votes'},\n"
        "        'y': {'min': 0, 'max': 1, 'step': 0.5, 'label': 'share'},\n"
        "        'lines': [\n"
        "            {'style': 'main', 'label': 'Yes', 'x': np.array([0.0, 1.0]),\n"
        "             'y': (0.0, np.log(yes))},\n"
        "        ],\n"
        "        'points': [{'x': 1, 'y': np.float64(yes)}],\n"
        "        'readouts': [{'label': f'share of {votes}', 'value': f'{yes:.4f}'}],\n"
        "        'description': f'The share of yes votes in the first {votes}',\n"
        "    }\n"
    ),
}


def test_a_chart_is_what_chart_py_draws_with_the_values_as_json_holds_it() -> None:
    answer = json.loads(chart(json.dumps(SHARES), json.dumps({"votes": 2})))
    assert answer == {
        "chart": {
            "x": {"min": 0, "max": 1, "step": 1, "label": "votes"},
            "y": {"min": 0, "max": 1, "step": 0.5, "label": "share"},
            "lines": [
                {"style": "main", "label": "Yes", "x": [0.0, 1.0], "y": [0.0, -0.6931471805599453]}
            ],
            "points": [{"x": 1, "y": 0.5}],
            "readouts": [{"label": "share of 2", "value": "0.5000"}],
            "description": "The share of yes votes in the first 2",
        },
        "problem": None,
    }


@pytest.mark.filterwarnings("ignore:divide by zero")
def test_a_value_that_is_not_finite_draws_nothing() -> None:
    files = {**SHARES, "data/votes.csv": "choice\nno\n"}
    answer = json.loads(chart(json.dumps(files), json.dumps({"votes": 1})))
    assert answer["chart"]["lines"][0]["y"] == [0.0, None]


def test_a_chart_that_fails_gives_the_error() -> None:
    answer = json.loads(chart(json.dumps(SHARES), json.dumps({"votes": 0})))
    assert answer == {
        "chart": None,
        "problem": {"kind": "ZeroDivisionError", "message": "division by zero"},
    }


def test_a_chart_whose_code_exits_gives_the_error() -> None:
    files = {**SHARES, "tally.py": "import sys\n\nsys.exit(1)\n"}
    answer = json.loads(chart(json.dumps(files), json.dumps({"votes": 2})))
    assert answer == {"chart": None, "problem": {"kind": "SystemExit", "message": "1"}}


def test_batch_mode_answers_a_chart_request() -> None:
    done = subprocess.run(
        [sys.executable, "sulba_runner.py"],
        input=json.dumps({"files": SHARES, "chart": {"votes": 3}}) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=Path(__file__).parents[1],
        check=True,
    )
    assert json.loads(done.stdout)["chart"]["readouts"] == [
        {"label": "share of 3", "value": "0.6667"}
    ]

import importlib
import sys

import pytest

from features import features, stays
from model import calls, chosen, threshold_for
from train import SHARE, save

pytest_plugins = ["pytester"]

# The files your tests run beside, copied for each run.
FILES = ["features.py", "model.py", "train.py", "app.py", "test_app.py"]
DATA = ["encounters.csv", "ids-mapping.csv"]
MODULES = ["app", "test_app", "conftest"]

# A conftest that plants one problem in your service: it wraps app.app, so every request
# your tests send meets the problem, and leaves the rest of the service as it is.
PLANTED = """
import json

import app as service

PROBLEM = None
DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]


def stays_in(path, body):
    if path == "/predict":
        return [body]
    if path == "/predict/batch":
        return body.get("stays", [])
    return []


def change_request(path, body):
    stays = [stay for stay in stays_in(path, body) if isinstance(stay, dict)]
    for stay in stays:
        days = stay.get("time_in_hospital")
        if PROBLEM == "longer stays" and isinstance(days, int) and days > 14:
            stay["time_in_hospital"] = 14
        if PROBLEM == "deaths" and stay.get("discharge_disposition_id") in DEATH_OR_HOSPICE:
            stay["discharge_disposition_id"] = 1
    full = path == "/predict/batch" and len(stays) == service.BATCH_LIMIT
    if PROBLEM == "full batch" and full:
        body["stays"].append(stays[0])
    return body


def change_answer(path, answer):
    if path == "/predict":
        predictions = [answer]
    elif path == "/predict/batch":
        predictions = answer["predictions"]
    else:
        return answer
    if PROBLEM == "half":
        for prediction in predictions:
            prediction["call"] = prediction["probability"] >= 0.5
    if PROBLEM == "order":
        predictions.reverse()
    return answer


class Planted:
    def __init__(self, inner):
        self.inner = inner

    def __getattr__(self, name):
        return getattr(self.inner, name)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.inner(scope, receive, send)
        body, more = b"", True
        while more:
            message = await receive()
            body += message.get("body", b"")
            more = message.get("more_body", False)
        try:
            body = json.dumps(change_request(scope["path"], json.loads(body))).encode()
        except ValueError:
            pass
        sent = False

        async def received():
            nonlocal sent
            if sent:
                return {"type": "http.disconnect"}
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        start, chunks = None, []

        async def answered(message):
            nonlocal start
            if message["type"] == "http.response.start":
                start = message
                return
            chunks.append(message.get("body", b""))
            if message.get("more_body", False):
                return
            content = b"".join(chunks)
            if start["status"] == 200:
                try:
                    answer = change_answer(scope["path"], json.loads(content))
                    content = json.dumps(answer).encode()
                except ValueError:
                    pass
            headers = [(k, v) for k, v in start["headers"] if k.lower() != b"content-length"]
            headers.append((b"content-length", str(len(content)).encode()))
            await send({**start, "headers": headers})
            await send({"type": "http.response.body", "body": content})

        await self.inner(scope, received, answered)


service.app = Planted(service.app)
"""


@pytest.fixture(scope="module")
def trained():
    """A model fitted on the extract's first 1,000 stays, with its threshold, recall and
    precision there: a stand-in for train's, quick to make."""
    table = stays("data/encounters.csv").head(1000)
    model = chosen(table)
    probabilities = model.predict_proba(features(table))[:, 1]
    threshold = threshold_for(probabilities, SHARE)
    _, recall, precision = calls(table["readmitted"], probabilities, threshold)
    return {
        "model": model,
        "threshold": threshold,
        "recall": recall,
        "precision": precision,
    }


# Each run counts outcomes, with no cache and no hunt for unraisable exceptions in the garbage,
# which takes a while at the end of each run. pytest explains a failed assertion through its
# terminal plugin, so the run on your service as it is keeps it, quietly.
QUIET = [
    "-p",
    "no:cacheprovider",
    "-p",
    "no:unraisableexception",
    "-p",
    "sulba_fixtures",
]
EXPLAINED = ["-q", "--tb=no"]
UNEXPLAINED = ["-p", "no:terminal", "-x"]


class Plain:
    """Formats a failure's traceback as Python does, rather than with each frame's source."""

    def pytest_configure(self, config):
        config.option.tbstyle = "native"


def first_failure(recorder):
    """The first of your tests that failed, and the first line of its error, or None."""
    failures = recorder.getfailures()
    if not failures:
        return None
    report = failures[0]
    crash = getattr(report.longrepr, "reprcrash", None)
    error = crash.message.splitlines()[0] if crash else "it failed"
    return f"{report.nodeid.split('::')[-1]}, with {error}"


# Each run of your tests: on your service as it is, then with each problem planted.
PROBLEMS = [None, "half", "longer stays", "order", "full batch", "deaths"]
# How many of your tests passed and failed in each run, once the first test has run them.
found = {}


@pytest.fixture
def outcomes(pytester, pytestconfig, trained):
    """How many of your tests pass and fail on your service, as it is and with each problem
    planted, all run by the first test that asks."""
    if found:
        return found
    root = pytestconfig.rootpath
    for name in FILES:
        (pytester.path / name).write_text((root / name).read_text())
    (pytester.path / "data").mkdir()
    for name in DATA:
        (pytester.path / "data" / name).write_bytes((root / "data" / name).read_bytes())
    save(trained)
    # Your service, started once: each run of your tests meets it as it is, or wrapped.
    for name in MODULES:
        sys.modules.pop(name, None)
    service = importlib.import_module("app")
    unwrapped = service.app
    try:
        for problem in PROBLEMS:
            options, plugins = [*QUIET, *EXPLAINED], []
            if problem:
                planted = PLANTED.replace("PROBLEM = None", f"PROBLEM = {problem!r}")
                (pytester.path / "conftest.py").write_text(planted)
                # One failing test is enough to catch the problem, and its error isn't shown.
                options, plugins = [*QUIET, *UNEXPLAINED], [Plain()]
            recorder = pytester.inline_run(*options, "test_app.py", plugins=plugins)
            passed, _, failed = recorder.countoutcomes()
            found[problem] = passed, failed, first_failure(recorder)
            service.app = unwrapped
            for name in ("test_app", "conftest"):
                sys.modules.pop(name, None)
    finally:
        for name in MODULES:
            sys.modules.pop(name, None)
    return found


@pytest.mark.id("tst_ohvp93")
def test_pass_on_your_service(outcomes):
    """Your tests pass on your service"""
    passed, failed, failure = outcomes[None]
    assert failed == 0, f"{failed} failed on your service, the first {failure}"
    assert passed > 0, "No tests of yours ran"


def caught(outcomes, problem):
    """Whether one of your tests failed on the service with the problem planted."""
    return outcomes[problem][1] > 0


@pytest.mark.id("tst_9oo0tl")
def test_catch_calls_at_half(outcomes):
    """They catch a service that calls at a probability of 0.5"""
    assert caught(outcomes, "half"), "Every one of your tests passed on it"


@pytest.mark.id("tst_z0zp1x")
def test_catch_longer_stays(outcomes):
    """They catch a service that answers for a stay of more than 14 days"""
    assert caught(outcomes, "longer stays"), "Every one of your tests passed on it"


@pytest.mark.id("tst_8u1we3")
def test_catch_batch_order(outcomes):
    """They catch a service that answers a batch out of order"""
    assert caught(outcomes, "order"), "Every one of your tests passed on it"


@pytest.mark.id("tst_syy3fo")
def test_catch_full_batch(outcomes):
    """They catch a service that refuses a full batch"""
    assert caught(outcomes, "full batch"), "Every one of your tests passed on it"


@pytest.mark.id("tst_46d3cy")
def test_catch_deaths(outcomes):
    """They catch a service that answers for a death or hospice care"""
    assert caught(outcomes, "deaths"), "Every one of your tests passed on it"

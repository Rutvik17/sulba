import hashlib
import http.server
import io
import json
import os
import signal
import subprocess
import sys
import tarfile
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import psycopg
import pytest

import sulba_fixtures
from sulba_runner import run

HERE = Path(__file__).parents[1]
# Postgres refuses to run as root, as CI's runners never are.
not_as_root = pytest.mark.skipif(
    os.name != "nt" and os.geteuid() == 0, reason="Postgres doesn't run as root"
)

SESSION = {
    "tests/test_store.py": """
import psycopg
import pytest
from pgvector.psycopg import register_vector
import numpy as np


@pytest.mark.id("tst_dtb001")
def test_nearest(database):
    with psycopg.connect(database) as conn:
        register_vector(conn)
        conn.execute("CREATE TABLE pages (id int PRIMARY KEY, embedding vector(3))")
        with conn.cursor() as cur, cur.copy("COPY pages FROM STDIN WITH (FORMAT BINARY)") as copy:
            copy.set_types(["int4", "vector"])
            copy.write_row((1, np.array([1.0, 0.0, 0.0])))
            copy.write_row((2, np.array([0.0, 1.0, 0.0])))
        found = conn.execute(
            "SELECT id FROM pages ORDER BY embedding <=> %s LIMIT 1", (np.array([0.9, 0.1, 0.0]),)
        ).fetchone()
    assert found == (1,)


@pytest.mark.id("tst_dtb002")
def test_empty(database):
    with psycopg.connect(database) as conn:
        tables = "SELECT count(*) FROM pg_tables WHERE schemaname = 'public'"
        assert conn.execute(tables).fetchone() == (0,)
        assert conn.execute("SHOW server_encoding").fetchone() == ("UTF8",)
        assert conn.execute("SHOW lc_messages").fetchone() == ("C",)
""",
}


@not_as_root
def test_each_test_gets_an_empty_database_with_pgvector() -> None:
    result = json.loads(run(json.dumps(SESSION), json.dumps(["tests/test_store.py"])))
    assert [(test["name"], test["status"], test["message"]) for test in result["tests"]] == [
        ("test_nearest", "pass", None),
        ("test_empty", "pass", None),
    ]


@not_as_root
@pytest.mark.skipif(sys.platform != "linux", reason="pgvector comes with embedded-postgres here")
def test_on_linux_the_server_runs_the_postgresql_projects_pgvector() -> None:
    server = sulba_fixtures.Postgres()
    try:
        with psycopg.connect(server.url("sulba_template")) as conn:
            version = "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
            assert conn.execute(version).fetchone() == ("0.8.7",)
            path = conn.execute("SHOW dynamic_library_path").fetchone()
            folder = sulba_fixtures.pgvector_folder()
            assert folder is not None
            assert path == (f"{folder / 'lib'}:$libdir",)
    finally:
        server.stop()


@not_as_root
def test_the_server_stops_and_leaves_nothing_behind(tmp_path: Path) -> None:
    import tempfile

    before = set(Path(tempfile.gettempdir()).glob("sulba-postgres-*"))
    run(json.dumps(SESSION), json.dumps(["tests/test_store.py"]))
    assert set(Path(tempfile.gettempdir()).glob("sulba-postgres-*")) == before


@not_as_root
@pytest.mark.skipif(os.name == "nt", reason="sends Ctrl+C as a POSIX signal")
def test_the_learners_database_keeps_its_data_until_it_is_deleted(tmp_path: Path) -> None:
    (tmp_path / ".sulba").mkdir()
    (tmp_path / ".sulba" / "lab.json").write_text(json.dumps({"stages": []}), encoding="utf-8")
    for name in ("sulba.py", "sulba_fixtures.py"):
        (tmp_path / name).write_text((HERE / name).read_text(encoding="utf-8"), encoding="utf-8")

    def serve() -> tuple[subprocess.Popen[str], str]:
        server = subprocess.Popen(
            [sys.executable, "sulba.py", "db", "--port", str(free_port())],
            cwd=tmp_path,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        assert server.stdout is not None
        line = server.stdout.readline()
        assert line.startswith("The database answers at postgresql://postgres:"), line
        return server, line.split(" at ")[1].split(". Press")[0]

    server, url = serve()
    with psycopg.connect(url) as conn:
        conn.execute("CREATE TABLE notes (text text)")
        conn.execute("INSERT INTO notes VALUES ('kept')")
        assert conn.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'").fetchone()
    server.send_signal(signal.SIGINT)
    assert server.communicate(timeout=60)[0] == "Stopped the database.\n"
    assert (tmp_path / ".sulba" / "database-password").stat().st_mode & 0o077 == 0
    server, url = serve()
    with psycopg.connect(url) as conn:
        assert conn.execute("SELECT text FROM notes").fetchall() == [("kept",)]
    server.send_signal(signal.SIGTERM)
    assert server.communicate(timeout=60)[0] == "Stopped the database.\n"


def test_the_cache_folder_is_placed_as_hugging_faces_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert sulba_fixtures.cache_folder() == tmp_path / "xdg" / "sulba"
    monkeypatch.delenv("XDG_CACHE_HOME")
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    assert sulba_fixtures.cache_folder() == tmp_path / "home" / ".cache" / "sulba"


CONTROL = """comment = 'vector data type and ivfflat and hnsw access methods'
default_version = '0.8.7'
module_pathname = '$libdir/vector'
relocatable = true
"""


def package() -> bytes:
    """A Debian package laid out as the PostgreSQL project's pgvector packages are."""
    files = {
        "./usr/lib/postgresql/18/lib/vector.so": b"\x7fELF",
        "./usr/lib/postgresql/18/lib/bitcode/vector/src/vector.bc": b"BC",
        "./usr/share/postgresql/18/extension/vector.control": CONTROL.encode(),
        "./usr/share/postgresql/18/extension/vector--0.8.7.sql": b"CREATE TYPE vector;",
        "./usr/share/postgresql/18/extension/vector--0.8.6--0.8.7.sql": b"",
        "./usr/share/doc/postgresql-18-pgvector/copyright": b"PostgreSQL License",
    }
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:xz") as packed:
        for name, contents in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(contents)
            packed.addfile(member, io.BytesIO(contents))
    archive = b"!<arch>\n"
    for name, contents in [
        ("debian-binary", b"2.0\n"),
        ("control.tar.xz", b"control"),
        ("data.tar.xz", data.getvalue()),
    ]:
        header = f"{name:<16}{0:<12}{0:<6}{0:<6}{100644:<8}{len(contents):<10}`\n"
        archive += header.encode() + contents + b"\n" * (len(contents) % 2)
    return archive


@pytest.fixture
def publisher(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[list[str]]:
    """The PostgreSQL project's packages, served from this machine, as on Linux on x86_64, with
    the cache folder in tmp_path. It gives the path of each request."""
    served = package()
    requests: list[str] = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            requests.append(self.path)
            self.send_response(200)
            self.send_header("Content-Length", str(len(served)))
            self.end_headers()
            self.wfile.write(served)

        def log_message(self, *args: Any) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    pinned = ("pgvector.deb", len(served), hashlib.sha256(served).hexdigest())
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.machine", lambda: "x86_64")
    monkeypatch.setattr(
        sulba_fixtures, "PGVECTOR_PACKAGES", f"http://127.0.0.1:{server.server_port}"
    )
    monkeypatch.setattr(sulba_fixtures, "PGVECTOR_BUILDS", {"x86_64": pinned})
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    yield requests
    server.shutdown()


def test_pgvector_for_linux_is_fetched_once_into_the_cache(
    publisher: list[str], tmp_path: Path
) -> None:
    folder = sulba_fixtures.pgvector_folder()
    assert folder is not None
    assert folder.parent == tmp_path / "sulba" / "pgvector"
    assert (folder / "lib" / "vector.so").read_bytes() == b"\x7fELF"
    assert sorted(path.name for path in (folder / "share" / "extension").iterdir()) == [
        "vector--0.8.6--0.8.7.sql",
        "vector--0.8.7.sql",
        "vector.control",
    ]
    # The server finds the library in its dynamic_library_path, not its own lib folder.
    assert (folder / "share" / "extension" / "vector.control").read_text(encoding="utf-8") == (
        CONTROL.replace("'$libdir/vector'", "'vector'")
    )
    assert sorted(path.name for path in folder.parent.iterdir()) == [folder.name]
    assert sulba_fixtures.pgvector_folder() == folder
    assert publisher == ["/pgvector.deb"]


def test_a_package_other_than_the_pinned_one_is_refused(
    publisher: list[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name, size, _ = sulba_fixtures.PGVECTOR_BUILDS["x86_64"]
    monkeypatch.setattr(sulba_fixtures, "PGVECTOR_BUILDS", {"x86_64": (name, size, "0" * 64)})
    with pytest.raises(RuntimeError, match="sent a different pgvector from the one the lab"):
        sulba_fixtures.pgvector_folder()
    assert not (tmp_path / "sulba").exists()


def test_pgvector_comes_with_embedded_postgres_elsewhere(
    publisher: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    assert sulba_fixtures.pgvector_folder() is None
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.machine", lambda: "riscv64")
    with pytest.raises(RuntimeError, match=r"pgvector has no build for Linux on riscv64\."):
        sulba_fixtures.pgvector_folder()
    assert publisher == []


def free_port() -> int:
    return sulba_fixtures.free_port()

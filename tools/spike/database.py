"""Spike: Postgres with pgvector on this machine, three ways, before the Retrieval module's
decision record.

- pixeltable-pgserver 0.6.0's Postgres 18 binaries, started with initdb and pg_ctl as a runner
  would start them, with a password, in folders whose names have a space and letters outside
  ASCII, and on Windows also in a folder from tempfile.mkdtemp;
- embedded-postgres 18.6.3, through its own get_server;
- PGlite 0.5.10 with pgvector, served by pglite-socket 0.2.13 on Node 24.22.0, each fetched and
  checked by size and sha256.

Each runs the same work on 10,000 clustered vectors of 1,024 numbers: loading them, exact search,
HNSW and IVFFlat builds and searches, and full-text search. Then it checks what one connection
leaves behind for the next. It prints what it found as JSON, and into the job's summary on GitHub
Actions.

    uv run --no-project --python 3.14 --with psycopg[binary]==3.3.6 --with pgvector==0.5.1 \
        --with numpy==2.4.6 --with pixeltable-pgserver==0.6.0 --with embedded-postgres==18.6.3 \
        tools/spike/database.py <folder for downloads and data>
"""

import hashlib
import importlib.util
import json
import os
import platform
import secrets
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import traceback
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

ROWS = 10_000
DIM = 1024
QUERIES = 100
NODE_VERSION = "24.22.0"
NODES = {
    ("Linux", "x86_64"): (
        f"node-v{NODE_VERSION}-linux-x64.tar.xz",
        32015600,
        "cc2f601cee82d9a5a233302fe307abc600727035fd7d2c3a3571755989e95008",
    ),
    ("Linux", "aarch64"): (
        f"node-v{NODE_VERSION}-linux-arm64.tar.xz",
        30943704,
        "fef00bb4d36e1c50104a9775a10359beee98f162b4104dd12472c75065c6a143",
    ),
    ("Windows", "AMD64"): (
        f"node-v{NODE_VERSION}-win-x64.zip",
        37733703,
        "f9683a19877e12a9b167305c8db71040d812876359de21f0d2e97c3f321f80c3",
    ),
    ("Darwin", "arm64"): (
        f"node-v{NODE_VERSION}-darwin-arm64.tar.gz",
        53049576,
        "6a9724d9b50a5f22b4816cded441b5a8d9ddae546191a5e5b7efa5a5e2ee26d5",
    ),
}
NPM = "https://registry.npmjs.org/@electric-sql"
PACKAGES = {
    "pglite": (
        f"{NPM}/pglite/-/pglite-0.5.10.tgz",
        10206211,
        "89dfe018869f30dd08a53e477f008c073d6e4770fdb1f21c66118523d43e373b",
    ),
    "pglite-socket": (
        f"{NPM}/pglite-socket/-/pglite-socket-0.2.13.tgz",
        77302,
        "e96b6acd932b14a7b33cce2799aebb40d94253f0e7e33e276856b447acf19c3a",
    ),
    "pglite-pgvector": (
        f"{NPM}/pglite-pgvector/-/pglite-pgvector-0.0.11.tgz",
        58067,
        "cea1ddde0b7dae07948f8b85a06e479dbc21e57e1038359750580a811aaa58a0",
    ),
    "pglite-pg_textsearch": (
        f"{NPM}/pglite-pg_textsearch/-/pglite-pg_textsearch-0.0.12.tgz",
        159861,
        "cc677752e76920a0cd36fee5e352b5731b86691c947c8d5a86977fc68173e092",
    ),
}
WORDS = (
    "bike brake chain wheel tyre saddle pedal gear frame spoke repair service booking price shop "
    "cable hub rim tube valve pump bearing crank derailleur lever grip fork headset"
).split()
WINDOWS = platform.system() == "Windows"


def fetched(url, size, sha256, path):
    """The file at path, fetched from url unless it's already there, checked by size and sha256."""
    if not path.exists() or path.stat().st_size != size:
        started = time.time()
        urllib.request.urlretrieve(url, path)
        print(f"fetched {url} in {time.time() - started:.1f} s", flush=True)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert path.stat().st_size == size, (path, path.stat().st_size)
    assert digest == sha256, (path, digest)
    return path


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def vectors(seed):
    """Clustered unit vectors, as embeddings are, and queries near some of them."""
    rng = np.random.default_rng(seed)
    centres = rng.standard_normal((64, DIM))
    docs = centres[rng.integers(0, 64, ROWS)] + 0.6 * rng.standard_normal((ROWS, DIM))
    docs /= np.linalg.norm(docs, axis=1, keepdims=True)
    queries = docs[rng.choice(ROWS, QUERIES, replace=False)] + 0.02 * rng.standard_normal(
        (QUERIES, DIM)
    )
    queries /= np.linalg.norm(queries, axis=1, keepdims=True)
    bodies = [" ".join(rng.choice(WORDS, 12)) for _ in range(ROWS)]
    return docs.astype(np.float32), queries.astype(np.float32), bodies


DOCS, QUERY_VECTORS, BODIES = vectors(0)
TRUTH = [set(np.argsort(-(DOCS @ q), kind="stable")[:10].tolist()) for q in QUERY_VECTORS]


def timed(out, key, work):
    started = time.time()
    value = work()
    out[key] = round(time.time() - started, 3)
    return value


def recall(conn):
    found = [
        {row[0] for row in conn.execute(
            "SELECT id FROM items ORDER BY embedding <=> %s LIMIT 10", (q,)
        ).fetchall()}
        for q in QUERY_VECTORS
    ]
    return round(sum(len(f & t) for f, t in zip(found, TRUTH)) / (10 * QUERIES), 3)


def work(url, copy=True, prepare_threshold=5):
    """Loads the vectors and searches them, timing each step."""
    out = {}
    with psycopg.connect(url, autocommit=True, prepare_threshold=prepare_threshold) as conn:
        out["server"] = conn.execute("SHOW server_version").fetchone()[0]
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)
        out["vector"] = conn.execute(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()[0]
        conn.execute("DROP TABLE IF EXISTS items")
        conn.execute(
            f"CREATE TABLE items (id int PRIMARY KEY, body text NOT NULL, embedding vector({DIM}) NOT NULL)"
        )

        def load_copy():
            with conn.cursor() as cur:
                with cur.copy(
                    "COPY items (id, body, embedding) FROM STDIN WITH (FORMAT BINARY)"
                ) as rows:
                    rows.set_types(["int4", "text", "vector"])
                    for i in range(ROWS):
                        rows.write_row((i, BODIES[i], DOCS[i]))

        def load_unnest():
            for start in range(0, ROWS, 500):
                ids = list(range(start, min(ROWS, start + 500)))
                conn.execute(
                    "INSERT INTO items SELECT * FROM unnest(%s::int[], %s::text[], %s::vector[])",
                    (ids, [BODIES[i] for i in ids], [DOCS[i] for i in ids]),
                )

        timed(out, "load_s", load_copy if copy else load_unnest)
        out["load"] = "COPY" if copy else "INSERT from unnest"

        def exact():
            return recall(conn)

        out["exact_recall"] = timed(out, "exact_100_queries_s", exact)
        conn.execute("SET maintenance_work_mem = '512MB'")
        timed(
            out,
            "hnsw_build_s",
            lambda: conn.execute("CREATE INDEX items_hnsw ON items USING hnsw (embedding vector_cosine_ops)"),
        )
        for ef in (10, 40, 100):
            conn.execute(f"SET hnsw.ef_search = {ef}")
            out[f"hnsw_ef{ef}_recall"] = timed(out, f"hnsw_ef{ef}_100_queries_s", exact)
        plan = conn.execute(
            "EXPLAIN SELECT id FROM items ORDER BY embedding <=> %s LIMIT 10",
            (QUERY_VECTORS[0],),
        ).fetchall()
        out["hnsw_used"] = any("items_hnsw" in row[0] for row in plan)
        conn.execute("DROP INDEX items_hnsw")
        timed(
            out,
            "ivfflat_build_s",
            lambda: conn.execute(
                "CREATE INDEX items_ivfflat ON items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
            ),
        )
        for probes in (1, 10):
            conn.execute(f"SET ivfflat.probes = {probes}")
            out[f"ivfflat_p{probes}_recall"] = timed(
                out, f"ivfflat_p{probes}_100_queries_s", exact
            )
        conn.execute("DROP INDEX items_ivfflat")
        timed(
            out,
            "fts_index_s",
            lambda: (
                conn.execute(
                    "ALTER TABLE items ADD COLUMN tsv tsvector "
                    "GENERATED ALWAYS AS (to_tsvector('english', body)) STORED"
                ),
                conn.execute("CREATE INDEX ON items USING gin (tsv)"),
            ),
        )
        out["fts_stems"] = conn.execute(
            "SELECT to_tsvector('english', 'Repairing the brakes of bikes')::text"
        ).fetchone()[0]
        out["fts_top"] = [
            row[0]
            for row in conn.execute(
                "SELECT id FROM items, websearch_to_tsquery('english', %s) q "
                "WHERE tsv @@ q ORDER BY ts_rank_cd(tsv, q) DESC, id LIMIT 5",
                ("brake repair",),
            ).fetchall()
        ]
        try:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_textsearch")
            timed(
                out,
                "bm25_index_s",
                lambda: conn.execute(
                    "CREATE INDEX items_bm25 ON items USING bm25 (body) WITH (text_config = 'english')"
                ),
            )
            out["bm25_top"] = [
                row[0]
                for row in conn.execute(
                    "SELECT id FROM items ORDER BY body <@> to_bm25query(%s, 'items_bm25'), id LIMIT 5",
                    ("brake repair",),
                ).fetchall()
            ]
        except psycopg.Error as error:
            out["bm25"] = f"{type(error).__name__}: {str(error).splitlines()[0]}"
        conn.execute("DROP TABLE items")
    return out


def sessions(url):
    """What one connection leaves behind for the next, and whether two can be open at once."""
    out = {}
    with psycopg.connect(url, autocommit=True) as first:
        first.execute("SET work_mem = '77MB'")
        for _ in range(6):
            first.execute("SELECT 1 + %s", (1,)).fetchone()
    try:
        with psycopg.connect(url, autocommit=True, connect_timeout=10) as second:
            out["setting_seen_by_next"] = second.execute("SHOW work_mem").fetchone()[0] == "77MB"
            try:
                for _ in range(6):
                    second.execute("SELECT 2 + %s", (2,)).fetchone()
                out["prepared_statements"] = "kept apart"
            except Exception as error:
                out["prepared_statements"] = f"{type(error).__name__}: {str(error).splitlines()[0]}"
    except Exception as error:
        out["second_connection"] = f"{type(error).__name__}: {str(error).splitlines()[0]}"
    try:
        with psycopg.connect(url, autocommit=True, connect_timeout=10) as a:
            with psycopg.connect(url, autocommit=True, connect_timeout=10) as b:
                a.execute("CREATE TABLE IF NOT EXISTS seen (n int)")
                with a.transaction():
                    a.execute("INSERT INTO seen VALUES (1)")
                    out["uncommitted_seen_by_other"] = (
                        b.execute("SELECT count(*) FROM seen").fetchone()[0] > 0
                    )
                a.execute("DROP TABLE seen")
        out["two_at_once"] = "yes"
    except Exception as error:
        out["two_at_once"] = f"{type(error).__name__}: {str(error).splitlines()[0]}"
    try:
        with psycopg.connect(url, autocommit=True, connect_timeout=10) as conn:
            started = time.time()
            conn.execute("CREATE DATABASE spike_copy")
            out["create_database_s"] = round(time.time() - started, 3)
            conn.execute("DROP DATABASE spike_copy")
    except Exception as error:
        out["create_database"] = f"{type(error).__name__}: {str(error).splitlines()[0]}"
    return out


def exe(name):
    return name + ".exe" if WINDOWS else name


def native(bin_dir, folder):
    """Starts Postgres from bin_dir in folder, as a runner would, runs the work and stops it."""
    out = {"folder": str(folder)}
    folder.mkdir(parents=True, exist_ok=True)
    data = folder / "pg"
    password = secrets.token_urlsafe(16)
    pwfile = folder / "password.txt"
    pwfile.write_text(password, encoding="utf-8")
    port = free_port()
    run = lambda args: subprocess.run(  # noqa: E731
        [str(a) for a in args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    started = time.time()
    done = run([
        bin_dir / exe("initdb"), "-D", data, "-U", "postgres", "-A", "scram-sha-256",
        f"--pwfile={pwfile}", "-E", "UTF8", "--locale=C", "--locale-provider=builtin",
        "--builtin-locale=C.UTF-8", "--no-instructions",
    ])
    out["initdb_s"] = round(time.time() - started, 2)
    if done.returncode != 0:
        out["initdb"] = (done.stdout + done.stderr)[-1500:]
        return out
    options = f"-p {port} -c listen_addresses=127.0.0.1"
    if not WINDOWS:
        options += " -c unix_socket_directories="
    started = time.time()
    done = run([
        bin_dir / exe("pg_ctl"), "-D", data, "-l", folder / "server.log", "-w", "-t", "60",
        "-o", options, "start",
    ])
    out["start_s"] = round(time.time() - started, 2)
    if done.returncode != 0:
        out["start"] = (done.stdout + done.stderr)[-1500:]
        log = folder / "server.log"
        if log.exists():
            out["server_log"] = log.read_text(encoding="utf-8", errors="replace")[-1500:]
        return out
    url = f"postgresql://postgres:{password}@127.0.0.1:{port}/postgres?sslmode=disable"
    try:
        out["work"] = work(url)
        out["sessions"] = sessions(url)
        try:
            with psycopg.connect(
                f"postgresql://postgres:wrong@127.0.0.1:{port}/postgres?sslmode=disable",
                connect_timeout=10,
            ):
                out["wrong_password"] = "accepted"
        except psycopg.OperationalError as error:
            out["wrong_password"] = str(error).splitlines()[-1][:200]
    finally:
        started = time.time()
        done = run([bin_dir / exe("pg_ctl"), "-D", data, "-w", "-m", "fast", "stop"])
        out["stop_s"] = round(time.time() - started, 2)
        if done.returncode != 0:
            out["stop"] = (done.stdout + done.stderr)[-500:]
    return out


def pixeltable(root):
    spec = importlib.util.find_spec("pixeltable_pgserver")
    bin_dir = Path(spec.origin).parent / "pginstall18" / "bin"
    out = {"bin": str(bin_dir)}
    for name in ("Dossier de données é", "Łódź 🚲"):
        try:
            out[name] = native(bin_dir, root / name)
        except Exception:
            out[name] = traceback.format_exc()[-1500:]
    if WINDOWS:
        try:
            out["mkdtemp"] = native(bin_dir, Path(tempfile.mkdtemp()) / "data")
        except Exception:
            out["mkdtemp"] = traceback.format_exc()[-1500:]
    return out


def embedded(root):
    import embedded_postgres

    out = {}
    started = time.time()
    with embedded_postgres.get_server(root / "embedded") as server:
        out["start_s"] = round(time.time() - started, 2)
        url = server.get_uri()
        out["uri"] = url
        out["work"] = work(url)
        out["sessions"] = sessions(url)
    return out


def node(root):
    """Node.js for this system, fetched and unpacked into root."""
    name, size, sha256 = NODES[(platform.system(), platform.machine())]
    archive = fetched(f"https://nodejs.org/dist/v{NODE_VERSION}/{name}", size, sha256, root / name)
    folder = root / "node"
    if not folder.exists():
        if name.endswith(".zip"):
            with zipfile.ZipFile(archive) as packed:
                packed.extractall(folder)
        else:
            with tarfile.open(archive) as packed:
                packed.extractall(folder, filter="tar")
    unpacked = next(folder.iterdir())
    return unpacked / "node.exe" if WINDOWS else unpacked / "bin" / "node"


def pglite(root):
    out = {}
    binary = node(root)
    modules = root / "pglite" / "node_modules" / "@electric-sql"
    for name, (url, size, sha256) in PACKAGES.items():
        archive = fetched(url, size, sha256, root / url.rsplit("/", 1)[1])
        target = modules / name
        if not target.exists():
            with tarfile.open(archive) as packed:
                packed.extractall(root / "unpack" / name, filter="tar")
            shutil.move(root / "unpack" / name / "package", target)
    out["node_modules_mb"] = round(
        sum(f.stat().st_size for f in modules.rglob("*") if f.is_file()) / 1e6, 1
    )

    def serve():
        port = free_port()
        server = subprocess.Popen(
            [
                str(binary),
                str(modules / "pglite-socket" / "dist" / "scripts" / "server.js"),
                "--db=memory://",
                f"--port={port}",
                "--extensions=@electric-sql/pglite-pgvector:vector,"
                "@electric-sql/pglite-pg_textsearch:pg_textsearch",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        lines = []
        ready = threading.Event()

        def read():
            for line in server.stdout:
                lines.append(line.rstrip())
                if "listening" in line:
                    ready.set()

        threading.Thread(target=read, daemon=True).start()
        started = time.time()
        if not ready.wait(120):
            server.kill()
            raise RuntimeError("\n".join(lines[-20:]))
        return server, port, round(time.time() - started, 2), lines

    server, port, out["start_s"], lines = serve()
    url = f"postgresql://postgres:postgres@127.0.0.1:{port}/postgres?sslmode=disable"
    try:
        out["work"] = work(url, copy=False, prepare_threshold=None)
        out["sessions"] = sessions(url)
    finally:
        server.kill()
        server.wait()
    server, port, _, lines = serve()
    url = f"postgresql://postgres:postgres@127.0.0.1:{port}/postgres?sslmode=disable"
    try:
        with psycopg.connect(url, autocommit=True) as conn:
            conn.execute("CREATE TABLE t (n int)")
            with conn.cursor() as cur:
                with cur.copy("COPY t (n) FROM STDIN") as rows:
                    for i in range(100):
                        rows.write_row((i,))
            out["copy"] = conn.execute("SELECT count(*) FROM t").fetchone()[0]
    except Exception as error:
        out["copy"] = f"{type(error).__name__}: {str(error).splitlines()[0]}"
    try:
        with psycopg.connect(url, autocommit=True, connect_timeout=10) as conn:
            out["after_copy"] = conn.execute("SELECT 1").fetchone()[0]
    except Exception as error:
        out["after_copy"] = f"{type(error).__name__}: {str(error).splitlines()[0]}"
    finally:
        server.kill()
        server.wait()
        out["server_log"] = lines[-8:]
    return out


def main():
    root = Path(sys.argv[1]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    found = {
        "system": f"{platform.system()} {platform.release()} {platform.machine()}",
        "cpus": os.cpu_count(),
        "python": sys.version.split()[0],
        "admin": (
            __import__("ctypes").windll.shell32.IsUserAnAdmin() != 0
            if WINDOWS
            else os.geteuid() == 0
        ),
    }
    for name, attempt in (("pixeltable", pixeltable), ("embedded", embedded), ("pglite", pglite)):
        started = time.time()
        try:
            found[name] = attempt(root)
        except Exception:
            found[name] = {"error": traceback.format_exc()[-2000:]}
        found[name + "_total_s"] = round(time.time() - started, 1)
        print(json.dumps({name: found[name]}, indent=1, ensure_ascii=False), flush=True)
    text = json.dumps(found, indent=1, ensure_ascii=False)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write(f"```json\n{text}\n```\n")


if __name__ == "__main__":
    main()

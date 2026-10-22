import threading

import psycopg
import pytest

from migrations import MIGRATIONS, Migration, MigrationError, migrate


def connect(database):
    return psycopg.connect(database, autocommit=True)


def columns(conn, table):
    return conn.execute(
        "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
        "WHERE table_name = %s ORDER BY ordinal_position",
        [table],
    ).fetchall()


@pytest.mark.id("tst_9lcmk9")
def test_every_migration_in_order(database):
    """An empty database gets every migration, in order, each recorded"""
    with connect(database) as conn:
        assert migrate(conn) == [1, 2, 3]
        recorded = conn.execute(
            "SELECT version, name, checksum FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert recorded == [(m.version, m.name, m.checksum) for m in MIGRATIONS]
        assert columns(conn, "conversations") == [
            ("id", "text", "NO"),
            ("page", "text", "YES"),
            ("started_at", "timestamp with time zone", "NO"),
        ]
        assert columns(conn, "messages") == [
            ("conversation_id", "text", "NO"),
            ("position", "integer", "NO"),
            ("role", "text", "NO"),
            ("content", "text", "NO"),
        ]
        assert columns(conn, "turns") == [
            ("id", "bigint", "NO"),
            ("conversation_id", "text", "NO"),
            ("started_at", "timestamp with time zone", "NO"),
            ("seconds", "double precision", "NO"),
            ("prompt_tokens", "integer", "NO"),
            ("completion_tokens", "integer", "NO"),
            ("outcome", "text", "NO"),
        ]


@pytest.mark.id("tst_m8bzhy")
def test_each_migration_once(database):
    """A second run applies nothing"""
    with connect(database) as conn:
        migrate(conn)
        assert migrate(conn) == []
        assert conn.execute("SELECT count(*) FROM schema_migrations").fetchone() == (3,)


@pytest.mark.id("tst_u014zm")
def test_a_new_migration(database):
    """A migration added later is the only one applied"""
    later = Migration(4, "notes", "ALTER TABLE conversations ADD COLUMN note text")
    with connect(database) as conn:
        migrate(conn)
        assert migrate(conn, [*MIGRATIONS, later]) == [4]
        assert ("note", "text", "YES") in columns(conn, "conversations")


@pytest.mark.id("tst_sw0z4u")
def test_a_changed_migration(database):
    """A migration changed after it was applied is refused, naming it"""
    changed = [*MIGRATIONS[:2], Migration(3, "turns", "CREATE TABLE turns (id int)")]
    with connect(database) as conn:
        migrate(conn)
        with pytest.raises(MigrationError, match="Migration 3, turns, has changed"):
            migrate(conn, changed)


@pytest.mark.id("tst_gtri6t")
def test_a_migration_that_fails(database):
    """A migration that fails changes nothing, and the ones before it stay applied"""
    failing = Migration(
        4, "broken", "CREATE TABLE notes (id int); ALTER TABLE nowhere ADD COLUMN x int"
    )
    with connect(database) as conn:
        with pytest.raises(psycopg.errors.UndefinedTable):
            migrate(conn, [*MIGRATIONS, failing])
        versions = conn.execute("SELECT version FROM schema_migrations ORDER BY 1")
        assert [row[0] for row in versions] == [1, 2, 3]
        assert conn.execute("SELECT to_regclass('notes')").fetchone() == (None,)
    # The lock went with the failure, so another app can take it.
    with connect(database) as other:
        other.execute("SET lock_timeout = '5s'")
        assert migrate(other) == []


@pytest.mark.id("tst_8hllsk")
def test_two_apps_at_once(database):
    """Two apps that start at once apply each migration once between them"""
    applied = []
    errors = []

    def start():
        try:
            with connect(database) as conn:
                applied.append(migrate(conn))
        except Exception as error:
            errors.append(error)

    threads = [threading.Thread(target=start) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert sorted(applied) == [[], [1, 2, 3]]


@pytest.mark.id("tst_6xxnuy")
def test_versions_in_order(database):
    """Versions out of order, or with a gap, are refused before anything runs"""
    with connect(database) as conn:
        for wrong in ([MIGRATIONS[1], MIGRATIONS[0]], [MIGRATIONS[0], MIGRATIONS[2]]):
            with pytest.raises(MigrationError):
                migrate(conn, wrong)
        assert conn.execute("SELECT to_regclass('schema_migrations')").fetchone() == (
            None,
        )


@pytest.mark.id("tst_m8abxe")
def test_what_the_tables_refuse(database):
    """The tables refuse a page, role or outcome that isn't one of theirs, and a conversation's
    messages and turns go with it"""
    with connect(database) as conn:
        migrate(conn)
        for bad in (
            "INSERT INTO conversations (id, page) VALUES ('c2', 'irs')",
            "INSERT INTO messages VALUES ('c1', 0, 'agent', 'Hi')",
            "INSERT INTO messages VALUES ('nowhere', 0, 'caller', 'Hi')",
        ):
            with pytest.raises(psycopg.errors.IntegrityError):
                conn.execute(bad)
        conn.execute("INSERT INTO conversations (id) VALUES ('c1')")
        conn.execute("INSERT INTO messages VALUES ('c1', 0, 'caller', 'Hi')")
        with pytest.raises(psycopg.errors.UniqueViolation):
            conn.execute("INSERT INTO messages VALUES ('c1', 0, 'desk', 'Hello')")
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                "INSERT INTO turns (conversation_id, started_at, seconds, prompt_tokens, "
                "completion_tokens, outcome) VALUES ('c1', now(), 2, 10, 5, 'cancelled')"
            )
        conn.execute(
            "INSERT INTO turns (conversation_id, started_at, seconds, prompt_tokens, "
            "completion_tokens, outcome) VALUES ('c1', now(), 2, 10, 5, 'done')"
        )
        conn.execute("DELETE FROM conversations WHERE id = 'c1'")
        assert conn.execute("SELECT count(*) FROM messages").fetchone() == (0,)
        assert conn.execute("SELECT count(*) FROM turns").fetchone() == (0,)

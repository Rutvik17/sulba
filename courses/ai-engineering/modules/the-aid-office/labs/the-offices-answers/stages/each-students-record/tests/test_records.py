import pytest
from index import connect
from office_records import AWARDS, STUDENTS
from records import ROLE, Award, Record, create, lines, load, record


def expected(student):
    """The student's record, from office_records."""
    [fafsa] = [has_fafsa for name, has_fafsa in STUDENTS if name == student]
    awards = sorted(
        (Award(*row[1:]) for row in AWARDS if row[0] == student),
        key=lambda award: award.award,
    )
    return Record(student, fafsa, awards)


@pytest.fixture
def conn(database):
    with connect(database) as conn:
        create(conn)
        load(conn)
        yield conn


@pytest.mark.id("tst_inu4f2")
def test_tables(conn):
    """Keeps both tables behind row-level security, readable by ROLE"""
    found = dict(
        conn.execute(
            "SELECT relname, relrowsecurity FROM pg_class "
            "WHERE relname IN ('students', 'awards')"
        ).fetchall()
    )
    assert found == {"students": True, "awards": True}
    [granted] = conn.execute(
        "SELECT has_table_privilege(%s, 'awards', 'SELECT')", (ROLE,)
    ).fetchone()
    assert granted


@pytest.mark.id("tst_o4yehf")
def test_record(conn):
    """Reads each student's own record"""
    for student, _ in STUDENTS:
        assert record(conn, student) == expected(student)


@pytest.mark.id("tst_f6guei")
def test_unknown(conn):
    """Gives None for a student the office doesn't have, quotes and all"""
    assert record(conn, "S9999") is None
    assert record(conn, "S1001' OR '1' = '1") is None


@pytest.mark.id("tst_rpvo4d")
def test_policy(conn):
    """Lets the role see only the student set for the transaction, and nobody without one"""
    with conn.transaction():
        conn.execute(f"SET LOCAL ROLE {ROLE}")
        assert conn.execute("SELECT count(*) FROM awards").fetchone() == (0,)
    with conn.transaction():
        conn.execute(f"SET LOCAL ROLE {ROLE}")
        conn.execute("SELECT set_config('app.student', 'S1002', true)")
        students = conn.execute("SELECT DISTINCT student FROM awards").fetchall()
    assert students == [("S1002",)]


@pytest.mark.id("tst_9xxr3x")
def test_nothing_kept(conn):
    """Leaves the connection as it found it after each record"""
    record(conn, "S1002")
    assert conn.execute("SELECT current_user = session_user").fetchone() == (True,)
    [left] = conn.execute("SELECT current_setting('app.student', true)").fetchone()
    assert left in ("", None)
    assert conn.execute("SELECT count(*) FROM awards").fetchone()[0] == len(AWARDS)


@pytest.mark.id("tst_6cts1z")
def test_lines():
    """Words each award, and a record with no FAFSA or no awards"""
    record = Record("S1", True, [Award("Federal Pell Grant", 3200, 3200, 1600)])
    assert lines(record) == [
        "Federal Pell Grant: offered $3,200, accepted $3,200, paid $1,600, $1,600 to come."
    ]
    assert lines(Record("S2", False, [])) == [
        "The office doesn't have your FAFSA for 2026-27."
    ]
    assert lines(Record("S3", True, [])) == ["You have no awards for 2026-27."]

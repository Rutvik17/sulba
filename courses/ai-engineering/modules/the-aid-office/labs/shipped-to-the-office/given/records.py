from dataclasses import dataclass

from office_records import AWARDS, STUDENTS

ROLE = "office_assistant"


@dataclass(frozen=True)
class Award:
    award: str
    offered: int
    accepted: int
    paid: int


@dataclass(frozen=True)
class Record:
    student: str
    fafsa: bool
    awards: list[Award]


def create(conn):
    """The tables students and awards, which ROLE reads only for the student named by the
    transaction's app.student."""
    conn.execute(
        "CREATE TABLE students (student text PRIMARY KEY, fafsa boolean NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE awards (student text NOT NULL REFERENCES students, award text NOT NULL, "
        "offered integer NOT NULL, accepted integer NOT NULL, paid integer NOT NULL, "
        "PRIMARY KEY (student, award))"
    )
    conn.execute(
        f"DO $$ BEGIN CREATE ROLE {ROLE} NOLOGIN; "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    )
    for table in ("students", "awards"):
        conn.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        conn.execute(
            f"CREATE POLICY own ON {table} FOR SELECT TO {ROLE} "
            "USING (student = current_setting('app.student', true))"
        )
        conn.execute(f"GRANT SELECT ON {table} TO {ROLE}")


def load(conn):
    """The office's students and awards, from office_records, into the tables."""
    with conn.cursor() as cur:
        cur.executemany("INSERT INTO students VALUES (%s, %s)", STUDENTS)
        cur.executemany("INSERT INTO awards VALUES (%s, %s, %s, %s, %s)", AWARDS)


def record(conn, student):
    """The student's record, read as ROLE with app.student set for one transaction, or None
    for a student the office doesn't have."""
    with conn.transaction():
        conn.execute(f"SET LOCAL ROLE {ROLE}")
        conn.execute("SELECT set_config('app.student', %s, true)", (student,))
        found = conn.execute("SELECT student, fafsa FROM students").fetchone()
        if found is None:
            return None
        awards = [
            Award(*row)
            for row in conn.execute(
                "SELECT award, offered, accepted, paid FROM awards ORDER BY award"
            )
        ]
    return Record(found[0], found[1], awards)


def lines(record):
    """The record as the office words it, a line for each award, dollars to the dollar."""
    if not record.fafsa:
        return ["The office doesn't have your FAFSA for 2026-27."]
    if not record.awards:
        return ["You have no awards for 2026-27."]
    return [
        f"{award.award}: offered ${award.offered:,}, accepted ${award.accepted:,}, "
        f"paid ${award.paid:,}, ${award.accepted - award.paid:,} to come."
        for award in record.awards
    ]

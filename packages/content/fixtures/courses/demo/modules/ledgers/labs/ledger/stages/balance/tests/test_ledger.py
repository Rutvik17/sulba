import psycopg
import pytest
from entries import amounts
from ledger import balance


@pytest.mark.id("tst_demo20")
def test_balance():
    """Adds up the ledger"""
    assert balance(amounts()) == 37


@pytest.mark.id("tst_demo21")
def test_empty():
    """An empty ledger balances at 0"""
    assert balance([]) == 0


@pytest.mark.id("tst_demo26")
def test_balance_in_postgres(database):
    """Postgres, with pgvector, adds up the ledger the same"""
    with psycopg.connect(database) as conn:
        conn.execute("CREATE TABLE entries (amount integer)")
        with conn.cursor() as cursor, cursor.copy("COPY entries (amount) FROM STDIN") as copy:
            for amount in amounts():
                copy.write_row((amount,))
        assert conn.execute("SELECT sum(amount) FROM entries").fetchone() == (balance(amounts()),)
        assert conn.execute("SELECT '[1, 2]'::vector <-> '[1, 4]'::vector").fetchone() == (2.0,)

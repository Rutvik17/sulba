import csv
from collections import defaultdict

import numpy as np
import psycopg
from sulba_fixtures import Postgres

K = 5
MORE = 20
EVERY = (
    "SELECT id FROM passages, websearch_to_tsquery('english', %(question)s) AS query "
    "WHERE words @@ query LIMIT 1"
)
# For a query of any word, ts_rank_cd counts 0.1 for each place one of its words is in the
# passage, so its order is a count, the same on every system.
ANY = (
    "WITH asked AS (SELECT replace(plainto_tsquery('english', %(question)s)::text, "
    "'&', '|')::tsquery AS query) "
    "SELECT id FROM passages, asked "
    "WHERE words @@ query ORDER BY ts_rank_cd(words, query) DESC, id LIMIT %(k)s"
)


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def figures():
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        passages = list(csv.DictReader(file))
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = [row for row in csv.DictReader(file) if row["set"] == "validation"]
    relevant = defaultdict(set)
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            relevant[row["question"]].add(row["passage"])
    server = Postgres()
    try:
        with psycopg.connect(
            server.url(server.new_database()), autocommit=True
        ) as conn:
            conn.execute(
                "CREATE TABLE passages (id text PRIMARY KEY, body text NOT NULL, words "
                "tsvector GENERATED ALWAYS AS (to_tsvector('english', body)) STORED)"
            )
            with (
                conn.cursor() as cursor,
                cursor.copy("COPY passages (id, body) FROM STDIN") as copy,
            ):
                for passage in passages:
                    copy.write_row((passage["passage"], passage["text"]))
            (weight,) = conn.execute(
                "SELECT ts_rank_cd(to_tsvector('english', 'benefits'), "
                "plainto_tsquery('english', 'benefits'))"
            ).fetchone()
            held = {
                word: conn.execute(
                    "SELECT count(*) FROM passages WHERE words @@ plainto_tsquery('english', %s)",
                    (word,),
                ).fetchone()[0]
                for word in ("benefit", "appeal")
            }
            none = found = found_more = 0
            for question in questions:
                asked = {"question": question["text"], "k": MORE}
                none += not conn.execute(EVERY, asked).fetchall()
                ranked = [id_ for (id_,) in conn.execute(ANY, asked)]
                found += not relevant[question["question"]].isdisjoint(ranked[:K])
                found_more += not relevant[question["question"]].isdisjoint(ranked)
    finally:
        server.stop()
    ids, vectors = read("data/passage-vectors.csv")
    question_ids, asked = read("data/question-vectors.csv")
    vector_of = dict(zip(question_ids, asked, strict=True))
    nearest = nearest_more = 0
    for question in questions:
        order = np.argsort(-(vectors @ vector_of[question["question"]]), kind="stable")
        rows = relevant[question["question"]]
        nearest += not rows.isdisjoint(ids[i] for i in order[:K])
        nearest_more += not rows.isdisjoint(ids[i] for i in order[:MORE])
    count = len(questions)
    return {
        "questions": str(count),
        "k": str(K),
        "more": str(MORE),
        "none": str(none),
        "weight": f"{weight:g}",
        "benefit_held": str(held["benefit"]),
        "appeal_held": str(held["appeal"]),
        "any": f"{found / count:.3f}",
        "any_more": f"{found_more / count:.3f}",
        "vectors": f"{nearest / count:.3f}",
        "vectors_more": f"{nearest_more / count:.3f}",
    }

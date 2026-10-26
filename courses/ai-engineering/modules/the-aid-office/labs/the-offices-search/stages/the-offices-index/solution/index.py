import csv
import hashlib
from dataclasses import dataclass

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

EMBEDDER = "nomic-embed-text-v1.5"
DOCUMENT = "search_document: "
BATCH = 32


@dataclass(frozen=True)
class Passage:
    id: str
    page: str
    title: str
    text: str


def read(path):
    """The passages in the file at path, in order."""
    with open(path, encoding="utf-8", newline="") as file:
        return [
            Passage(row["passage"], row["page"], row["title"], row["text"])
            for row in csv.DictReader(file)
        ]


def connect(url):
    conn = psycopg.connect(url, autocommit=True)
    register_vector(conn)
    return conn


def create(conn):
    conn.execute(
        "CREATE TABLE passages ("
        "id text PRIMARY KEY, page text NOT NULL, title text NOT NULL, "
        "body text NOT NULL, digest text NOT NULL, embedding vector(768) NOT NULL, "
        "words tsvector GENERATED ALWAYS AS "
        "(to_tsvector('english', title || ' ' || body)) STORED)"
    )
    conn.execute("CREATE INDEX ON passages USING hnsw (embedding vector_cosine_ops)")
    conn.execute("CREATE INDEX ON passages USING gin (words)")


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def embedded(client, texts):
    """The texts' vectors from the model, BATCH texts a request."""
    vectors = []
    for start in range(0, len(texts), BATCH):
        inputs = [DOCUMENT + text for text in texts[start : start + BATCH]]
        response = client.post("/embeddings", json={"model": EMBEDDER, "input": inputs})
        response.raise_for_status()
        data = sorted(response.json()["data"], key=lambda item: item["index"])
        vectors += [np.array(item["embedding"], dtype=np.float32) for item in data]
    return vectors


def sync(conn, client, passages):
    """Make the table hold the passages: the ones it lacks added, the rest removed,
    and only the new and changed texts embedded. Gives the ids of the passages
    embedded, in order."""
    kept = {
        id_: (page, title, kept_digest)
        for id_, page, title, kept_digest in conn.execute(
            "SELECT id, page, title, digest FROM passages"
        )
    }
    changed = [
        p for p in passages if p.id not in kept or kept[p.id][2] != digest(p.text)
    ]
    moved = [
        p
        for p in passages
        if p.id in kept
        and kept[p.id][2] == digest(p.text)
        and kept[p.id][:2] != (p.page, p.title)
    ]
    vectors = embedded(client, [p.text for p in changed])
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            "DELETE FROM passages WHERE NOT (id = ANY(%s))", ([p.id for p in passages],)
        )
        cur.executemany(
            "INSERT INTO passages (id, page, title, body, digest, embedding) "
            "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET "
            "page = EXCLUDED.page, title = EXCLUDED.title, body = EXCLUDED.body, "
            "digest = EXCLUDED.digest, embedding = EXCLUDED.embedding",
            [
                (p.id, p.page, p.title, p.text, digest(p.text), vector)
                for p, vector in zip(changed, vectors, strict=True)
            ],
        )
        cur.executemany(
            "UPDATE passages SET page = %s, title = %s WHERE id = %s",
            [(p.page, p.title, p.id) for p in moved],
        )
    return [p.id for p in changed]

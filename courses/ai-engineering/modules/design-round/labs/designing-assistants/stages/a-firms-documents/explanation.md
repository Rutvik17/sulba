## What it must do

Every answer comes from documents the person asking may read, and no answer, citation or count gives away a document they may not. Access changes often, as people join and leave matters, so the design has to follow it closely, and the firm has to be able to see who found what.

## The index

Each document is split into passages, about {% $fig.per_document %} each, so {% $fig.documents %} documents make {% $fig.passages %} passages. Each passage keeps its embedding, its text, its document's id, source and version, and its document's groups. Searches use both the passages' words and their embeddings, as in Hybrid search and reranking.

## Access at question time

The person's groups come from their sign-in, as in Inside the customer's walls, or from the directory, never from anything in the question. The search looks only at passages whose groups include one of the person's: the filter is part of the search. Taking the best passages first and dropping the forbidden ones after can leave a person on few matters with almost nothing, and a ranking that saw forbidden passages can still reveal them through what it kept. In Postgres with pgvector, the filter goes in the query's `WHERE`, with iterative index scans so that the search goes on until it has enough permitted passages.

## In step with the sources

Each source sends its changes to the indexer through a change feed or a scan every few minutes. A new or edited document is split and embedded again. A deleted document's passages are deleted at once. A change of access only rewrites the groups on the document's passages, with no embedding, so it costs little and can run within a minute.

## The answer

The model sees only the permitted passages and cites the documents they came from. Each citation links to the document in its source, which checks access again when the person opens it.

## Audit

Each search is logged with a pseudonym for the person, their groups, the time and the documents found, not the question's text, so the firm can answer "who saw this document?" without keeping what people asked.

## Size

{% $fig.passages %} passages of {% $fig.dimensions %} numbers at {% $fig.number_bytes %} bytes each is {% $fig.vector_bytes %} bytes a passage and about {% $fig.vector_gb %} of vectors, before the HNSW graph and the text. Storing each number in {% $fig.half_bytes %} bytes halves the vectors to about {% $fig.half_gb %}.

## The follow-up questions

- **Leaving a group at {% $fig.leaves_at %}:** if the groups come from the sign-in token, the old groups last until the token is replaced. Looking the groups up in the directory at question time, cached for {% $fig.cache_seconds %} seconds, means answers stop using the matter within that time.
- **Shared by mistake for an hour:** anyone whose search found the document in that hour could have read from it. The audit log lists those searches and who made them, so the firm knows exactly who to ask. Once access is fixed, the change reaches the passages within a minute.
- **Slower at {% $fig.later_passages %} passages:** that is about {% $fig.later_gb %} of vectors. First check that searches still use the index with the filter, and how far the iterative scans go for a person on few matters. A partial index for each of the largest groups, or numbers in {% $fig.half_bytes %} bytes, come next.

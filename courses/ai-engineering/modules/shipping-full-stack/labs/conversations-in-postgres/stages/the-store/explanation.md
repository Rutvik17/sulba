A pool keeps connections open between requests. psycopg's documentation explains why: "Because the time to establish a new connection can be relatively long, keeping connections open can reduce latency." A request borrows a connection and gives it back as its block ends. When every connection is lent, the next request waits for one.

The pool's connections are in autocommit mode, and a transaction is a block that says where it starts and ends. By default, psycopg starts a transaction with the first statement and keeps it open until a commit. Its documentation warns that "even a simple SELECT will start a transaction: in long-running programs, if no further action is taken, the session will remain idle in transaction, an undesirable condition for several reasons (locks are held by the session, tables bloat…)".

A turn is kept whole: the caller's message, the reply and what the turn used, in one transaction. A failure partway through, such as a usage the table refuses, leaves the conversation as it was, rather than holding a message with no reply.

Two turns kept at once would each count the conversation's messages, find the same number, and both write at that position. `FOR UPDATE` on the conversation's row makes them take turns. Postgres's documentation says it "prevents them from being locked, modified or deleted by other transactions until the current transaction ends", so the second turn counts once the first has committed.

Every value is a parameter. psycopg's documentation warns: "Don't manually merge values to a query". A value written into the SQL is read as SQL. Postgres reads a parameter only as a value, whatever its quotes and semicolons.

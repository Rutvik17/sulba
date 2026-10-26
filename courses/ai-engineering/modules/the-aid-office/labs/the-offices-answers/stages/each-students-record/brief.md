Students ask about their own aid too: what they were offered, what's been paid and what's to come. The office's records hold it, and a student must see their own and nobody else's, whatever their question says. Postgres can hold that line itself, with row-level security: a policy on each table names the rows a role may read.

`office_records.py`, which the lab gives you, holds the office's records for 2026-27, for {% $fig.students %} fictional students: `STUDENTS`, each student's id and whether the office has their FAFSA, and `AWARDS`, {% $fig.awards %} awards, each with its student, its name and the dollars offered, accepted and paid. Each test gets a new, empty database, through a connection that owns what it makes.

In `records.py`, write:

- `create(conn)`: the table `students`, with each student's `student`, text, its primary key, and `fafsa`, a boolean; and `awards`, with each award's `student`, which references `students`, and `award`, both text, its primary key the two together, and `offered`, `accepted` and `paid`, integers, none of them null. Make the role `ROLE`, which can't log in, unless it's there, and grant it `SELECT` on both tables. Turn on row-level security on both, each with a policy that lets `ROLE` read only the rows whose `student` is the setting `app.student`.
- `load(conn)`: the office's students and awards, from `office_records`, into the tables.
- `record(conn, student)`: the student's `Record`, their `student`, `fafsa` and `awards`, each an `Award` of its name and dollars, in the order of their names; or `None` for a student the office doesn't have. Read it as `ROLE`, with `app.student` the student, for one transaction alone, and leave the connection's role and settings as they were.
- `lines(record)`: the record as the office words it, a line for each award, such as `Federal Pell Grant: offered $3,200, accepted $3,200, paid $1,600, $1,600 to come.` A record with no FAFSA is the one line `The office doesn't have your FAFSA for 2026-27.`, and one with no awards `You have no awards for 2026-27.`

```
create(conn)
load(conn)
record(conn, student) -> Record or None
lines(record) -> list of str
```

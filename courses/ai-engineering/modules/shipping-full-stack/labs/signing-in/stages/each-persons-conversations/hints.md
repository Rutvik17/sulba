`ALTER TABLE conversations ADD COLUMN owner bigint REFERENCES people ON DELETE CASCADE` adds the column, and the conversations already there have no owner.

---

`WHERE id = %s AND owner = %s` finds a conversation only for its owner, in one query, so there's nothing to compare afterwards.

---

`ORDER BY started_at DESC, id LIMIT %s` lists the newest first, with the id to settle conversations started at the same moment.

The office's auditors want a line for every search: when it ran, who ran it, in which groups, and which documents it found. They don't want the person's name or email in the log, nor what they asked, which can name a caller. Each person goes in the log under a pseudonym that only the office, holding its key, can link back to them.

In `audit.py`, write:

- `pseudonym(key, subject)`: the first 16 hex digits of the subject's HMAC-SHA256 under `key`.
- `entry(key, staff, found, at)`: the line, as JSON on one line, with `at`, the time in UTC to the second, as `2026-11-02T09:30:15Z`; `who`, the pseudonym; `groups`, the person's groups in alphabetical order; and `documents`, the ids of the documents found, in their order. A time that doesn't know its time zone raises `ValueError`.

```
pseudonym(key, subject) -> str
entry(key, staff, found, at) -> str
```

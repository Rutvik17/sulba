The office's chat page sends each question to one function, with the student signed in, or no one, and what the question is about: the student's own aid, from the page's My aid button, or anything else, for the office's pages. Write it in `desk.py`:

- `create_tickets(conn)`: the table `tickets`, with each ticket's `id`, an integer identity, its primary key, its `student` and `question`, text, and `asked`, a `timestamptz` that is the time it was written unless one is given, none of them null.
- `respond(conn, client, student, question, about="pages")`: the `Reply` to the question: its `text`, the `pages` it cites, and whether it goes `to_staff`. `student` is the id of the student signed in, or `None` when no one is.

With `about` `"my aid"`, the reply is the student's record, as your `lines` words it, a line each, joined by newlines, and nothing goes to the model. A visitor who isn't signed in gets `SIGN_IN`, and a student the office has no record of `NO_RECORD`.

Otherwise, the reply is your `answer`. When it goes to staff, a student signed in gets it with a ticket, their id and the question in `tickets`, for the office's staff to reply to by email. A visitor gets `STAFF_SIGNED_OUT`, to staff, and no ticket, since there's no one to reply to.

```
create_tickets(conn)
respond(conn, client, student, question, about="pages") -> Reply
```

Two tests run on every attempt. Then five checks run before the code ships.

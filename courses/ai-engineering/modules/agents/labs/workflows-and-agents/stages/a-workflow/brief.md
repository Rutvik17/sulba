In a workflow, the model does one thing at a time, and code decides what happens next. The desk's workflow sorts the caller's first message into a route, with one request whose reply follows `ROUTE`, a JSON schema: its `kind`, which is `question`, `case`, `callback` or `other`, and the `service`, `day`, `time` and `part` of the day the message names, each `none` when it names none. Then code follows the route's path:

- A **question** is answered by a second request, with `ANSWER` as its system prompt and, in the caller's message, the passages the desk's search finds for the question in the service's pages, each as `[id] title`, a newline and its text, then the question.
- A **case** for a service is offered a ticket for that service's advisers, with the caller's message as its summary.
- A **callback** for a service on a day is offered on the caller's open ticket for the service, or on a new ticket when they have none: at the time asked, or the first free time in the part of the day asked, or the first free time that day. When the caller has more than one open ticket for the service, `ask` asks which; when no free time fits, the desk gives the times its advisers are free.
- Anything else gets `ask`.

An offer waits for the caller. The ticket or callback is made only when their next message starts with a yes, as `YES` matches it, and the reply says what was done, with the time of a callback. Any other message drops the offer and is sorted as a new message.

In `workflow.py`, write `route(client, message, page)`, the route of a message, with `ROUTER` as the system prompt, followed by `f" They opened the chat on the {SERVICES[page]} pages."` when the chat was opened from a service's pages. A service the message doesn't name is the page's. A reply that isn't JSON, lacks a field, or sorts the message as anything but a question, a case or a callback is `Route("other")`.

Then `Workflow`, one conversation. `reply(message, found=None)` gives the desk's reply to the caller's next message, and sets the desk's `turn` to the number of messages before it, from 0. `found` is the message's route when it has been sorted already, so that the workflow doesn't sort it again.

```
route(client, message, page) -> Route
Workflow(client, desk, page).reply(message, found=None) -> str
```

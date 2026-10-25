The contact centre has sent a brief for a demo next week:

> Messages from our web form land in one inbox. We'd like the desk to file each into the queue that handles it before anyone reads it: `benefits` for Social Security and retirement, `veterans` for VA benefits, `licences` for driving licences and IDs, and `student-aid` for student loans and grants. Anything else, or anything it isn't sure of, goes to `agent`. The demo needs to show us that:
>
> 1. Each message is filed to one of those five queues, and only those.
> 2. A Social Security number in a message never reaches the model.
> 3. When the model's answer can't be read, it's asked once more, and a second answer that can't be read goes to `agent`.
> 4. When the model is down or doesn't answer, the message goes to `agent` rather than nowhere.

In `triage.py`, write `triage(client, message)`, which gives the queue's name. `client` is an `httpx.Client` whose base URL is the model's API, as the desk's own clients are. Ask with a chat request to `/chat/completions` for `MODEL`, a system message that names every queue in `QUEUES`, and the message as the user's, and give the request a timeout of `TIMEOUT` seconds. The model answers with JSON such as `{"queue": "benefits"}`, which can come inside a Markdown code block.

A Social Security number is nine digits, as three, two and four, with a hyphen or a space between each group or none. It's sent as `[number removed]`, and the rest of the message as it was.

```
triage(client, message) -> str
```

The workflow does what it can follow quickly and in few requests, and the agent handles what doesn't fit a path. The desk's router puts them together: the model sorts the caller's first message, as the workflow's `route` does, and a route the workflow can follow goes down its path, while any other goes to the agent, which keeps the conversation from there.

In `router.py`, write `Router`, one conversation:

- `follows(found)` says whether the workflow follows a route;
- `reply(message)` gives the desk's reply to the caller's next message.

What the router must do:

- sort a conversation once, by its first message, and keep it on the path that message took;
- give the workflow a question, a case for a service, or a callback for a service on a day when the caller has at most one open ticket for that service, with the route already found, so that it isn't sorted twice;
- give the agent everything else.

How it does so is yours to choose.

```
Router(client, desk, page).follows(found) -> bool
Router(client, desk, page).reply(message) -> str
```

Four tests run on every attempt. Then three checks run before the code ships.

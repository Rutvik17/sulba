`await run_in_threadpool(store.keep, conversation.id, usage, messages)` runs the store's work on a worker thread and waits for it, while the event loop goes on with other requests.

---

Start the outcome at `left`, the one way of ending that no `except` sees. Set it where each other way is handled, and keep the turn in `finally` unless it's done.

---

A caller who leaves cancels the route through anyio, and anyio cancels again at every `await` until the route ends. `with anyio.CancelScope(shield=True):` around the store's work in `finally` lets that work finish.

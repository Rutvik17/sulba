A lock is for the cache's map, not for the call. `sync.Mutex` "is a mutual exclusion lock", and "If the lock is already in use, the calling goroutine blocks until the mutex is available." Held across `upstream.Chat`, it made every request through the cache wait for one model's reply, the cached ones too. The fix locks twice, once to look and once to store, and each hold lasts as long as a map access.

Two callers can now ask for the same request at once, both miss, and both ask the upstream. That costs one extra reply, and both store the same answer. A gateway with many identical requests at once could put `golang.org/x/sync/singleflight` in front of the upstream, which "provides a duplicate function call suppression mechanism": its `Do` makes "sure that only one execution is in-flight for a given key at a time", and "the duplicate caller waits for the original to complete and receives the same results."

A model's reply depends on every message before it, so the key has to as well. "How many people live there?" means something different after each question, and a key of the last message gave one conversation the other's answer. `json.Marshal(request)` writes the model, each message and the request's options, so two requests share a key only when they would ask the upstream the same thing.

A failure isn't an answer. The assistant's `store` kept the empty `Reply` that comes with an error, and the cache served it as a success for the rest of its time to live. An error has to reach the caller, so `Fallback` and `Retry` can act on it, and the next request has to reach the upstream.

The cache still keeps every request it has seen until that request comes again, so a gateway with many different requests would need a limit on the entries it keeps.

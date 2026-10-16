The service checks each sample's code against the clinic's registry of patients, a web service that takes a moment to answer each lookup. superstruct's checks are synchronous: a check gives its answer before the next line runs. A lookup that waited on the network that way would hold the whole service up while it waited, so the service's lookups are coroutines, which wait without holding anything else up.

The starter holds `Registry`, a stand-in for the registry: `await registry.lookup(code)` gives `True` or `False` after its `latency` in seconds. Write:

```
check_code(code, registry) -> None when the registry knows code, or
    No patient has the code 'S00003'
check_codes(codes, registry) -> each code's check, in order, one lookup after another
first_unknown(codes, registry) -> the first code the registry doesn't know, or None,
    asking about no code after it
```

`async def` makes a coroutine function, and `await` waits for a coroutine's result, as they do in JavaScript. A JavaScript async function starts when it's called, and runs as far as its first `await` straight away. Calling a coroutine function only makes a coroutine: nothing in it runs until it's awaited. An event loop runs coroutines, and while one waits, it runs the others. The tests run yours on one, and read the time it says passed.

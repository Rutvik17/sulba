The office's network team asks for one thing more before the desk goes in: that no request it makes leaves the office, however a model's reply, a document or a provider's answer is worded. Its own services are in `walls.py`'s `ALLOWED`: its model server and its sign-in.

In `walls.py`, write `Walled(inner, allowed=ALLOWED)`, an `httpx.AsyncBaseTransport` the desk's clients send through. It passes a request on to `inner` only when the request's host is one of `allowed`, and otherwise raises `NotAllowed` without sending it. Closing it closes `inner`.

What the transport must do:

- allow a host by its whole name only;
- match names in any case;
- refuse a host in disguise, by redirect, after a user name, or as a number;
- refuse with an error the desk's code already handles.

How it does so is yours to choose.

```
Walled(inner, allowed=ALLOWED) -> httpx.AsyncBaseTransport
```

Two tests run on every attempt. Then four checks run before the code ships.

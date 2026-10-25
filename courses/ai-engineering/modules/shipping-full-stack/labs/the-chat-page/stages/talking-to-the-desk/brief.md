The desk from Signing in has an API for a page: each person's own conversations, their replies, `/me` and `/usage`. The page is TypeScript, and everything it asks the desk goes through `Desk` in `api.ts`. The `Desk` you're given works while every answer is a success. Make it right for the rest:

- `#json` sends `Accept: application/json` with every request, and a body, with `Content-Type: application/json`, only when there is one. A GET has no body.
- An answer that isn't a success throws the `ApiError` that `failure(response)` makes. When the answer is `application/problem+json` or `application/json`, the error takes its `title`, `detail` and `errors`. Otherwise its title is the answer's status text, or `The desk answered 502.` when there's none, and its detail is `null`.
- `conversation(id)` puts the id into the address encoded, with `encodeURIComponent`.
- `usage(days)` asks for a whole number of days from 1 to 90, and for any other number gives a promise rejected with a `RangeError`, without asking the desk.
- `say(id, content, signal)` posts `{"content": ...}` to the conversation's messages with `Accept: text/event-stream`, passes the caller's `signal` on to `fetch`, throws as the JSON requests do when the desk refuses, and otherwise gives the response, whose body is the reply's event stream.
- The `fetch` the desk is given, the browser's unless a test gives another, is called on its own, not as a method of the desk.

```ts
new Desk(fetcher?: typeof fetch)
desk.say(id: string, content: string, signal?: AbortSignal): Promise<Response>
failure(response: Response): Promise<ApiError>
```

The tests give the desk a `fetch` of their own, which answers each request as the desk would.

The help desk's agent from Tools and planning answers one caller, in a terminal. This lab puts it behind a web API that many callers use at once. The lab gives you two files to build on. `desk.py` is the desk as Tools and planning built it: the help pages' search, the caller's tickets and the advisers' free times, the tools, and the tickets and callbacks the desk makes on a yes. Its search asks the embedding model through an `httpx.AsyncClient`. `agent.py` is the agent, which streams its reply as events.

A conversation comes first. In `conversations.py`, write `Conversations`, which keeps every conversation in memory, by its id:

- `start(page)` keeps a new conversation, opened from the help pages of one service or from none, with an id no one can guess, and gives it.
- `get(conversation_id)` gives the conversation, or `None`.
- `add(conversation_id, message)` adds a message to it.

Every error the app gives is a problem details object, as RFC 9457 defines it:

- `problem(status, detail=None, headers=None, **extensions)` gives a `JSONResponse` with the status, the headers and the media type `application/problem+json`. Its body has `type`, `about:blank`; `title`, the status's phrase, such as `Not Found`; `status`; `detail`, when there is one; and each extension.
- `pointer(location)` gives where in the request's body a validation error is, from its location, such as `("body", "page")`, as a JSON Pointer in a URI fragment: `#/page`. Inside a key, `~` is written `~0` and `/` is written `~1`, and a character a URI fragment can't hold is percent-encoded, as in `#/first%20name`.
- `install(app)` gives every HTTP error as problem details, with its headers, and with its detail unless that's only the status's phrase. That covers your own errors and FastAPI's, such as a 404 for an address the app doesn't have, or a 405 for a method it doesn't take. A request whose body doesn't fit gets a 422 with the detail `The request's content doesn't fit.`, and `errors`, which gives each error's message as its `detail`, and its `pointer`.

Then two routes, on `router`, each taking the app's conversations from `held`:

- `POST /conversations` takes a `Start`, whose only field is `page`, and refuses any other field. It starts a conversation and answers 201, with the conversation and its address, `/conversations/<id>`, in `Location`.
- `GET /conversations/{conversation_id}` gives the conversation, or a 404 with the detail `There's no conversation with this id.`

```
Conversations().start(page) -> Conversation
problem(status, detail=None, headers=None, **extensions) -> JSONResponse
pointer(location) -> str
install(app) -> None
POST /conversations
GET /conversations/{conversation_id}
```

The tests send their requests to the app in process, through httpx.

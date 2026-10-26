On the office's server, a reply from Qwen3.5-0.8B takes seconds to write, and a student waiting for the whole of it sees nothing until it's done. The desk shows the reply as the model writes it, then says what became of it: the answer with the pages it cites, or the question passed to staff, whose message takes the reply's place.

The lab gives you the office's code as you built it: the search in `index.py`, `search.py`, `scope.py` and `office.py`, and the answers, records and desk in `answers.py`, `records.py` and `desk.py`. Each test gets the office's {% $fig.passages %} passages indexed and a scripted model server, which streams each reply in the pieces the test gives it.

In `streamed.py`, write `stream(conn, client, question)`: a generator of the answer to the question, as the model writes it. It gives a `Piece` for each piece of the reply's text, as it comes, and ends with one `Verdict`, the answer's `text`, the `pages` it cites and whether it goes `to_staff`.

`stream` asks as `answer` in `answers.py` does, with the same request and a `stream` of `true`, through `client.stream`. The model sends the reply as server-sent events: a line `data: ` and a chunk of JSON for each piece, whose `choices` hold the piece in `delta`'s `content` and, in the last chunk, the `finish_reason`, then `data: [DONE]`. The verdict sends the question to staff, with `TO_STAFF`, in every case `answer` does: the search finds no page, which needs no request at all, the reply says it doesn't know, cites nothing, or doesn't come. It does too when the reply stopped for any reason but `"stop"`, such as `"length"`, the token limit.

```
stream(conn, client, question) -> Piece, ..., Verdict
```

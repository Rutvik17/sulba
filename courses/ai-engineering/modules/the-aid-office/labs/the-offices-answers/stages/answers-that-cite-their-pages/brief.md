The office's search gives pages. Now its assistant answers from them, with Qwen3.5-0.8B, which the office serves on the same machine, and each answer shows the student the pages it comes from.

The lab gives you the office's search as you built it, in `index.py`, `search.py`, `scope.py` and `office.py`. Its `find(conn, client, question)` gives the pages that best answer a question, best first, each as a `(page, id)` pair with its best passage, and none for a question the pages don't answer. Each test gets the office's {% $fig.passages %} passages indexed, and a scripted model server that embeds the office's questions with their recorded vectors and answers chat requests as the test scripts it.

In `answers.py`, write:

- `cited(reply, pages)`: the pages a reply cites, `pages` giving the page of each passage the model was given, in order, `[1]` naming the first. Give each page once, in the order the reply first cites it, and leave out a number that names no passage.
- `answer(conn, client, question)`: the `Answer` to a question: its `text`, the `pages` it cites, and whether it goes `to_staff`.

`answer` gives the question to `find`. When `find` gives no pages, the question goes to staff without asking the model. Otherwise it asks the model once, with a POST to `client`'s `/chat/completions` naming `MODEL`, for at most `MAX_TOKENS` tokens, with a timeout of `TIMEOUT` seconds. The system message is `INSTRUCTIONS`. The user message holds each passage `find` gave, in its order, after its number in brackets, from `[1]`, with its page's title on the number's line and its text on the next, the passages a blank line apart, then a blank line and the question after `Question: `.

The answer is the reply, stripped, with the pages it cites. It goes to staff, with `STAFF` for its text and no pages, when the reply says `I don't know` anywhere in it, in any case, cites no passage, or doesn't come: an error status, a dropped connection or no reply in time.

```
cited(reply, pages) -> list of pages
answer(conn, client, question) -> Answer
```

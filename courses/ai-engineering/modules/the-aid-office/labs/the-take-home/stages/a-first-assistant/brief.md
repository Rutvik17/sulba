Harbor College's financial aid office answers students' questions about federal student aid from Federal Student Aid's help pages. It wants an assistant that answers the questions those pages answer and passes the rest to its staff. Build a first version in `assistant.py`.

`data/pages.csv` holds the office's {% $fig.pages %} pages, each with its `page`, its `title` and its `text`, whose blocks a blank line divides. `data/questions.csv` holds {% $fig.questions %} questions students asked, each with the `page` that answers it. Write:

```
passages(path) -> the pages' passages, in order, each a Passage of its page, title and text
Search(passages) -> a search over the passages, built once
Search.best(question, k) -> the k passages that best answer the question, best first
answer(client, search, question) -> an Answer of the reply's text, the pages it cites, and
    whether the question goes to staff
```

A passage is one page's blocks, joined in order with a blank line between them, until another block would take it past `WORDS` words, a block's words being `block.split()`. A block longer than that is a passage of its own.

The search can work however you choose, but it must never give a passage that shares no word with the question, and for at least {% $fig.bar %} of the office's questions, the page that answers the question must be among the pages of its `BEST` best passages.

`answer` asks the model once, with a POST to `client`'s `/chat/completions`. The request names `MODEL`, and its messages are a system message of `INSTRUCTIONS` and a user message that gives each of the question's best passages after its number in brackets, from `[1]`, then the question. The reply cites passages by those numbers, and the answer is the reply with the pages of the passages it cites, in the order it first cites them, each once. A number that names no passage is left out.

The question goes to staff as `Answer(STAFF, [], True)` when the search finds no passage, without asking the model, and when the reply is `I don't know`, cites no passage, or doesn't come.

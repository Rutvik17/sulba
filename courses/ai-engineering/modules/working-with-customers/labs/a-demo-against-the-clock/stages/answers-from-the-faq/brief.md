The contact centre's second brief:

> We keep answers to the questions people ask most, in `faq.py`'s `FAQ`. For the pilot, the desk should answer from those answers only, and say which it used. The demo needs to show us that:
>
> 1. The model is shown the three answers that share the most words with the question, and none of the others.
> 2. Every reply cites at least one of the answers it was shown, and we can see which.
> 3. A reply that cites none of them, or cites one it wasn't shown, never reaches the caller: they're told an adviser will reply instead.
> 4. A question that shares no words with any answer gets the same, without asking the model.
> 5. When the model is down or doesn't answer, the caller gets the same.

In `faq.py`, write `answer(client, question, faq=FAQ)`, which gives an `Answer`: the reply and the ids it cites, in the order it first cites them, or `HANDOVER` and no ids. `client` is an `httpx.Client` whose base URL is the model's API. Ask with a chat request to `/chat/completions` for `MODEL`, the question as the user's message, and a system message that lists each answer shown on lines of its own, starting with its id in square brackets:

```
[f1] When is the office open?
Monday to Friday, 8:30 to 4:30, except on public holidays.
```

Give the request a timeout of `TIMEOUT` seconds. A reply cites an answer with its id in square brackets, such as `[f1]`.

Words are compared in lower case, without punctuation, and a word of fewer than four letters doesn't count; an answer's words are those of its question and its answer. Of the answers that share a word with the question, the three that share the most are shown, the earlier in `faq` first where two share as many.

```
answer(client, question, faq=FAQ) -> Answer
```

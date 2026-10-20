The help desk answers people with Qwen3.5-2B, from the first {% $fig.shown %} passages its reranked search finds. Before it changes its prompt, its model or its search, it needs questions to measure each change on: a development set to try changes against, and a test set it reports on and never tunes on.

`data/questions.csv` holds {% $fig.questions %} questions people opened their conversations with, about {% $fig.pages %} of the help pages, each with its page and its service. Questions about one page are answered from the same text, so a page with questions on both sides would let what was tuned on one side pass for a gain on the other. And some people asked the same thing in the same words.

In `testset.py`, write:

- `unique(questions)`: the questions in order, each one with the same words as an earlier one left out. `words` gives a question's words.
- `split(questions, share, rng)`: the ids of the unique questions, as a development set and a test set, each in the order of `questions`. Take the services in alphabetical order. For each one, list its pages in the order their first questions come, and draw `rng.permutation` of how many there are. Move its pages to the test set in that order, each with all its questions, until the test set holds at least `share` of the service's questions. The rest are the development set.

Each question is a row of `data/questions.csv` as `csv.DictReader` reads it, with its `question`, `page`, `domain` and `text`.

```
unique(questions) -> list of questions
split(questions, share, rng) -> (development, test)
```

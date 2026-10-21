BEGIN's replies are about sentences from Wikipedia, a line or two each, and a grader that agrees with people there may judge replies from the help desk's longer passages differently. No one has labelled the help desk's replies, but its dataset holds a reply people wrote to each of its {% $fig.questions %} questions, in `data/human-replies.csv`, from the passages of the question's page that hold the answer, its own passages. With them, a reply should keep to its context. With the own passages of a question from another service, it should say something its context doesn't: a reply about Social Security can't be put down to a page about driving licences.

In `known.py`, write:

- `own(question, relevant, passages)`: the question's own passages, those of `relevant` on its page, in the order given. `question` is a row of `data/questions.csv`, `relevant` the passages `data/relevant.csv` gives it, and `passages` maps each name to its row of `data/passages.csv`.
- `partners(questions)`: each question's partner, from the rows of `questions.csv` in order: the question half the list further on, going round from the end to the start, or the first after it from another service.
- `error_rates(labels, verdicts)`: the grader's misses, the share of the replies labelled 1 that it calls 0, and its false alarms, the share of those labelled 0 that it calls 1.

"Half the list further on" is `len(questions) // 2` places on. `data/human-grades.csv` holds the grader's sums of `Yes` and `No` for each reply with its own passages, with its partner's, and with the passage the help desk's search ranks first on another page of the same service that holds none of their texts.

```
own(question, relevant, passages) -> [name]
partners(questions) -> {question: question}
error_rates(labels, verdicts) -> (misses, false_alarms)
```

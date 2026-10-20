Some help pages repeat a paragraph another page holds: the help desk's {% $fig.passages %} passages hold {% $fig.texts %} texts, and {% $fig.repeated %} of those texts are in more than one passage. `data/relevant.csv` judges every copy of an answer relevant. Judged passage by passage, a search that shows a second copy of an answer scores again, though the reader learns nothing new, and a search that shows each text once loses for each copy it leaves out. The help desk will judge its searches as a reader sees them: by their texts.

In `texts.py`, write:

- `first_passages(texts)`: given each passage's text, each passage's text as the first passage in `texts` that holds it.
- `as_seen(shown, first)`: the passages shown as a reader sees them, at the same ranks: each as its text's first passage, or `None` if a passage before it showed the same text.
- `relevant_texts(relevant, first)`: the relevant passages' texts, each as its first passage.

The measures in `measures.py` then judge texts as they judge passages: `ndcg(as_seen(shown, first), relevant_texts(relevant, first), k)` is a question's nDCG by text.

```
first_passages(texts) -> dict[str, str]
as_seen(shown, first) -> list[str | None]
relevant_texts(relevant, first) -> set[str]
```

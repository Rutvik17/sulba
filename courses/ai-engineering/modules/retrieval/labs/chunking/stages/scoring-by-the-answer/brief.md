Passages marked relevant to a question score a search only while the pages are cut into those passages. To compare ways of cutting them, a search can be scored by the answer itself: `data/answers.csv` holds each part of the page a question's answer was given from, as its first character and the one after its last, and `data/questions.csv` gives each question's page.

Each part of an answer, and each chunk, is a place: its page, its first character and the one after its last. An answer's parts never overlap, but chunks can. In `score.py`, write:

- `recall(parts, found)`: the share of the answer's characters that one or more of the found chunks hold.
- `precision(parts, found)`: the share of the found chunks' characters that are the answer's, a character two chunks hold counted twice, or 0.0 when no chunk is found.
- `iou(parts, found)`: the intersection over the union: the answer's characters the found chunks hold, divided by the answer's characters plus the chunks', counted as precision counts them, less the ones held.
- `holding(parts, chunks)`: the chunks that hold one or more of the answer's characters, in their order.

```
recall(parts, found) -> float
precision(parts, found) -> float
iou(parts, found) -> float
holding(parts, chunks) -> list of (page, start, end)
```

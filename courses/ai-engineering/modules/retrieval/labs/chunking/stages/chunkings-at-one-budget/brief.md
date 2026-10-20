Scored by the answer, every way of cutting the pages can be searched with the same questions. `data/question-vectors-256.csv` holds each question's vector, and `data/vectors-<chunking>.csv` each chunk's for each chunking in `data/chunks.csv`, in the same order: from the lab's model, shortened to 256 numbers as its card shortens them, and stored as whole numbers, each number times 32,767. The help desk hands the model what its search finds, so the chunkings are compared at one budget of words: the chunks most similar to a question are taken until the next would take their words past it.

In `compare.py`, write:

- `ranked(question, vectors)`: the rows of `vectors`, the most similar to `question` first, by the dot product of their whole numbers, a tie going to the earlier row.
- `within(order, words, budget)`: the rows in `order`, until the next would take their words past `budget`. `words` gives each row's words.
- `compared(questions, answers, places, vectors, words, budget)`: the mean recall, precision and IoU over the questions of a search at `budget` words for each question's vector, scored with your `score.py`. `answers` gives each question's parts, and `places`, `vectors` and `words` each chunk's place, vector and words.

```
ranked(question, vectors) -> np.ndarray of rows
within(order, words, budget) -> list of rows
compared(questions, answers, places, vectors, words, budget) -> (recall, precision, iou)
```

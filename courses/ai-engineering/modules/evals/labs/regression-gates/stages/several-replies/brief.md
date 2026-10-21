The help desk's model writes at a temperature of {% $fig.temperature %}, so a question asked twice gets two different replies. A test set scored on one reply to each question measures that draw as well as the release. `data/replies.csv` holds {% $fig.samples %} replies of each of {% $fig.releases %} releases to each of the {% $fig.questions %} questions of the test set, from {% $fig.pages %} pages, each drawn with a seed of its own, with the reason the model stopped:

| Release | Shows the model | Its prompt asks for |
| --- | --- | --- |
| `current` | the first 5 passages of the reranked search | two or three sentences, each passage cited |
| `rerun` | the same, run again with other seeds | the same |
| `three-passages` | the first 3 | the same |
| `unranked` | the first 5 of the search before reranking | the same |
| `warmer` | the first 5 of the reranked search | a warm, complete answer, each passage cited |

Sample `k` of a question has the same seed in every release but the rerun. `data/relevant.csv` holds the passages that hold each question's answer, and `data/questions.csv` each question's page.

In `samples.py`, write:

- `cites_answer(reply, relevant)`: 1.0 if the reply cites a passage in `relevant`, each cited as `p` and its number in square brackets, and 0.0 if not.
- `scores(replies, relevant, questions, release, samples)`: the release's replies scored with `cites_answer`, a row for each question in `questions` and a column for each sample in `samples`, in their orders. `replies` holds rows of `data/replies.csv` as `csv.DictReader` reads them, and `relevant` maps each question to its set of passages.
- `standard_error(scores, pages)`: the standard error of the release's score, the mean `m` of its question means `q_i`, with each page's questions counted together.
- `sampling_variance(scores)`: what sampling adds to the variance of a question's mean: the mean over the questions of their samples' variance, with `K - 1` below, over `K`, the number of samples.

```math
\begin{aligned}
q_i &= \frac{1}{K} \sum_{k} s_{ik} \qquad m = \frac{1}{n} \sum_{i} q_i \\
\mathrm{SE} &= \frac{1}{n} \sqrt{\frac{G}{G-1} \sum_{g} \Bigl( \sum_{i \in g} (q_i - m) \Bigr)^2} \\
\sigma^2_{\text{sampling}} &= \frac{1}{n} \sum_{i} \frac{1}{K} \cdot \frac{1}{K-1} \sum_{k} (s_{ik} - q_i)^2
\end{aligned}
```

The tests compare your standard errors with statsmodels'.

```
cites_answer(reply, relevant) -> float
scores(replies, relevant, questions, release, samples) -> array of shape (len(questions), len(samples))
standard_error(scores, pages) -> float
sampling_variance(scores) -> float
```

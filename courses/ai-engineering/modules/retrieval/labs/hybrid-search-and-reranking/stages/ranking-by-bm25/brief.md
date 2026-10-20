Full-text search counted a question's words in each passage, each word the same. BM25 weighs them: a word that few passages hold counts for more, each time a passage holds a word again counts for less than the time before, and a long passage's words count for less than a short one's. `references/bm25.json` holds the scores bm25s, a Python library, gives the help desk's passages for each validation question, in its default form of BM25, Lucene's.

In `bm25.py`, write:

- `words(text)`: the text's runs of letters, digits and underscores, lowercased.
- `BM25(passages)`: an index of the passages, each given as its words.
- `scores(question)`: each passage's score for the question's words, a word counted as many times as the question holds it, and a word no passage holds adding nothing.
- `top(question, k)`: the rows of the `k` passages with the highest scores, a tie going to the earlier passage.

A passage's score is a sum over the question's words `$w$`:

```math
\text{score}(p) = \sum_{w} \text{idf}(w) \, \frac{f(w, p)}{f(w, p) + k_1 \left(1 - b + b \, \frac{\lvert p \rvert}{m}\right)}
```

```math
\text{idf}(w) = \ln\left(1 + \frac{N - n(w) + 0.5}{n(w) + 0.5}\right)
```

| Symbol | Meaning |
| --- | --- |
| `$f(w, p)$` | How many times passage `$p$` holds the word |
| `$\lvert p \rvert$` | How many words `$p$` has |
| `$m$` | The mean of `$\lvert p \rvert$` over the passages |
| `$N$` | How many passages there are |
| `$n(w)$` | How many of them hold the word |
| `$k_1$` | {% $fig.k1 %} |
| `$b$` | {% $fig.b %} |

```
words(text) -> list of words
BM25(passages)
scores(question) -> np.ndarray of each passage's score
top(question, k) -> list of rows
```

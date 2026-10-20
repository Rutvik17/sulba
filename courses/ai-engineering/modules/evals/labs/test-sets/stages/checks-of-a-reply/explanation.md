On the {% $fig.test %} test questions, with at most {% $fig.most %} words:

| Check | Share of replies that pass |
| --- | --- |
| `cites` | {% $fig.cites %} |
| `cites_shown` | {% $fig.cites_shown %} |
| `cites_answer` | {% $fig.cites_answer %} |
| `finished` | {% $fig.finished %} |
| `brief` | {% $fig.brief %} |
| `all` | {% $fig.all %} |

{% $fig.invented %} replies cite a passage they weren't shown: a name the model made up, which no reader could follow. The search showed a passage that holds the answer for {% $fig.held %} questions, {% $fig.held_share %} of them, and the reply cites one for {% $fig.cited_of_held %} of those. The rest of the misses are the search's: no reply can cite an answer it wasn't shown. Half the replies run past {% $fig.median_words %} words, the longest to {% $fig.longest %}, for a prompt that asks for two or three sentences.

Each check is cheap and exact, so it can run on every reply of every release. None of them says whether what a reply states is in the passages it cites: a reply can cite the right passage and still add a date, a fee or a step the passage never gives. That takes a reader, or a model trained to judge it.

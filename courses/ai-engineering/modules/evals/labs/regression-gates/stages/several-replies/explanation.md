The current release on the test set, with its rerun's replies after its own for ten replies a question. Each standard error is the root mean square over the replies taken one at a time ({% $fig.subsets_1 %} sets), in pairs ({% $fig.subsets_2 %}), in fives ({% $fig.subsets_5 %}) and all together, so that no one draw stands for its size:

| Replies to each question | Standard error | Sampling's share of the variance of the question means |
| --- | --- | --- |
| 1 | {% $fig.error_1 %} | {% $fig.share_1 %} |
| 2 | {% $fig.error_2 %} | {% $fig.share_2 %} |
| 5 | {% $fig.error_5 %} | {% $fig.share_5 %} |
| 10 | {% $fig.error_10 %} | {% $fig.share_10 %} |

A question's mean over `K` replies varies for two reasons: the question itself, which the release finds easy or hard, and the replies drawn for it. Sampling's part, the questions' sample variance over `K`, falls as `1/K`, and the question's part doesn't fall at all. With one reply a question, sampling makes up {% $fig.share_1 %} of the spread between question means; with five, {% $fig.share_5 %}. What is left is which questions the test set holds, which more replies to the same questions can't change: past a few replies, more questions narrow the margin and more replies hardly do.

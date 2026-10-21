Each release's five replies a question against the current release's, at {% $fig.confidence %}:

| Candidate | Score | Change | Margin, paired | Margin, unpaired | Correlation of question means |
| --- | --- | --- | --- | --- | --- |
| `rerun` | {% $fig.rerun_score %} | {% $fig.rerun_change %} | ±{% $fig.rerun_paired %} | ±{% $fig.rerun_unpaired %} | {% $fig.rerun_correlation %} |
| `three-passages` | {% $fig.three_passages_score %} | {% $fig.three_passages_change %} | ±{% $fig.three_passages_paired %} | ±{% $fig.three_passages_unpaired %} | {% $fig.three_passages_correlation %} |
| `unranked` | {% $fig.unranked_score %} | {% $fig.unranked_change %} | ±{% $fig.unranked_paired %} | ±{% $fig.unranked_unpaired %} | {% $fig.unranked_correlation %} |
| `warmer` | {% $fig.warmer_score %} | {% $fig.warmer_change %} | ±{% $fig.warmer_paired %} | ±{% $fig.warmer_unpaired %} | {% $fig.warmer_correlation %} |

The current release scores {% $fig.base %}. A question one release finds hard, the other mostly does too: the question means of the rerun and the current release correlate at {% $fig.rerun_correlation %}. The difference takes that shared part out, and what is left is the replies' own variation and how the releases differ. Comparing the two scores alone leaves it in, so its margin is as wide as two releases on different questions would give. Comparing the scores alone would take {% $fig.rerun_ratio %} times as many questions to give the rerun's paired margin, and {% $fig.unranked_ratio %} times as many for the unranked search, whose question means correlate least with the current release's.

The unranked search shows the model other passages, and for a page's questions it shows the same ones, so it moves a page's questions together: its margin is wider than the others'. A change to the prompt, or a rerun, moves each question on its own.

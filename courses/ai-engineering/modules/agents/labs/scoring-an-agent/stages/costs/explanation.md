Each task's median over its {% $fig.trials %} trials, and over the desk's {% $fig.tasks %} tasks the median and the 90th percentile of those, each with its {% $fig.confidence %} interval:

| | First tools | New tools |
| --- | --- | --- |
| Median, seconds | {% $fig.last_seconds_median %}, from {% $fig.last_seconds_median_low %} to {% $fig.last_seconds_median_high %} | {% $fig.this_seconds_median %}, from {% $fig.this_seconds_median_low %} to {% $fig.this_seconds_median_high %} |
| 90th percentile, seconds | {% $fig.last_seconds_p90 %}, from {% $fig.last_seconds_p90_low %} to {% $fig.last_seconds_p90_high %} | {% $fig.this_seconds_p90 %}, from {% $fig.this_seconds_p90_low %} to {% $fig.this_seconds_p90_high %} |
| Median, tokens | {% $fig.last_tokens_median %}, from {% $fig.last_tokens_median_low %} to {% $fig.last_tokens_median_high %} | {% $fig.this_tokens_median %}, from {% $fig.this_tokens_median_low %} to {% $fig.this_tokens_median_high %} |
| 90th percentile, tokens | {% $fig.last_tokens_p90 %}, from {% $fig.last_tokens_p90_low %} to {% $fig.last_tokens_p90_high %} | {% $fig.this_tokens_p90 %}, from {% $fig.this_tokens_p90_low %} to {% $fig.this_tokens_p90_high %} |

The new tools' typical task took less time, {% $fig.this_seconds_median %} seconds against {% $fig.last_seconds_median %}, though the two intervals meet between {% $fig.last_seconds_median_low %} and {% $fig.this_seconds_median_high %}. The 90th percentiles' intervals are wider and overlap more: only {% $fig.past_p90 %} of the {% $fig.tasks %} tasks lie past the 90th percentile, against half of them past the median, so the slow tenth is measured on far fewer tasks. In tokens, the two agents' intervals overlap at both percentiles.

A task's trials are alike. The slowest task on the first tools, by its median, took {% $fig.last_slowest_runs %} seconds: slow on every trial. Taking all {% $fig.runs %} runs as separate draws puts the 90th percentile at {% $fig.last_pooled_p90 %} seconds, from {% $fig.last_pooled_p90_low %} to {% $fig.last_pooled_p90_high %}, an interval narrower than the tasks' own; on the new tools, at {% $fig.this_pooled_p90 %}, from {% $fig.this_pooled_p90_low %} to {% $fig.this_pooled_p90_high %}. SciPy's documentation says of the test and its intervals: "They are valid if and only if the observations are i.i.d." A task's {% $fig.trials %} trials aren't {% $fig.trials %} independent draws, so the narrower interval claims more than the runs can show.

A task's median also holds against a bad run or two. The slowest task on the new tools took {% $fig.this_slowest_runs %} seconds, and its median is {% $fig.this_slowest_median %}, whatever its two slowest runs took.

The interval assumes nothing about how the costs are spread. Each task's median falls below the true p-quantile with the chance p, so how many of the {% $fig.tasks %} fall below it is binomial, and the ends are the sorted values at the counts that leave a chance of at most a on each side.

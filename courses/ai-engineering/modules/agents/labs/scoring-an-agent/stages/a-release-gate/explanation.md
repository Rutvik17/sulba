The gate on the desk's two agents, each in turn the candidate to replace the other, at k = {% $fig.k %}, a tolerance of {% $fig.tolerance %} and a budget of {% $fig.budget %} seconds, over the {% $fig.tasks %} tasks, with {% $fig.confidence %} intervals:

| Candidate | pass^{% $fig.k %} less the current agent's | 90th percentile of seconds | Held for |
| --- | --- | --- | --- |
| New tools | {% $fig.new_difference %}, from {% $fig.new_difference_low %} to {% $fig.new_difference_high %} | {% $fig.new_tail %}, from {% $fig.new_tail_low %} to {% $fig.new_tail_high %} | {% $fig.new_held %} |
| First tools | {% $fig.first_difference %}, from {% $fig.first_difference_low %} to {% $fig.first_difference_high %} | {% $fig.first_tail %}, from {% $fig.first_tail_low %} to {% $fig.first_tail_high %} | {% $fig.first_held %} |

Neither agent can replace the other at these settings. The new tools' slow tenth is within the budget even at its interval's high end, but on these tasks their pass^{% $fig.k %} may be lower than the first tools' by more than {% $fig.tolerance %}. The first tools may be as reliable, but their slow tenth may be over {% $fig.budget %} seconds.

The intervals are wide because they come from {% $fig.tasks %} tasks, and their margins shrink with the square root of the number of tasks. More trials of the same tasks make each task's estimate surer, but leave the spread between tasks as it is. A gate that can't decide asks for more tasks, or for a tolerance and a budget the desk can accept.

A gate is a rule set before the runs, so that what it decides isn't chosen after seeing them: the same `k`, tolerance and budget for every candidate.

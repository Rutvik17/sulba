At a level of {% $fig.alpha %} and a power of {% $fig.power %}, on the test set's {% $fig.questions %} questions:

| Comparison | Standard error of the change | Smallest drop found |
| --- | --- | --- |
| A rerun, one reply a question | {% $fig.rerun_error_1 %} | {% $fig.detectable_1 %} |
| A rerun, five replies a question | {% $fig.rerun_error_5 %} | {% $fig.detectable_5 %} |
| The unranked search, five replies a question | {% $fig.unranked_error %} | {% $fig.unranked_detectable %} |

For a comparison of two releases, more replies do help: the questions' own difficulty drops out of each difference, so the replies' variation is most of what is left, and five replies a question bring the drop the test set can find from {% $fig.detectable_1 %} to {% $fig.detectable_5 %}.

The unranked search scored {% $fig.unranked_drop %} lower than the current release. Its standard error is wider than a rerun's, since it moves a page's questions together, and a test at this level finds a drop of that size only {% $fig.unranked_power %} of the time. Finding it {% $fig.power %} of the time would take {% $fig.unranked_needed %} questions spread as these are. A gate on this test set can be counted on for drops of about {% $fig.unranked_detectable %} from a change to the search; a smaller one can pass, and its interval says so.

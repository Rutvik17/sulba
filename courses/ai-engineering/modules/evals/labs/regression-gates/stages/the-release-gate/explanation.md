The gate on each candidate against the current release, each score at {% $fig.level %}, {% $fig.alpha %} over {% $fig.scores %}, with its interval:

| Candidate | `cites_answer` | `finished` | `brief` | Gate |
| --- | --- | --- | --- | --- |
| `rerun` | {% $fig.rerun_cites_answer %} ({% $fig.rerun_cites_answer_interval %}) | {% $fig.rerun_finished %} ({% $fig.rerun_finished_interval %}) | {% $fig.rerun_brief %} ({% $fig.rerun_brief_interval %}) | {% $fig.rerun_verdict %} |
| `three-passages` | {% $fig.three_passages_cites_answer %} ({% $fig.three_passages_cites_answer_interval %}) | {% $fig.three_passages_finished %} ({% $fig.three_passages_finished_interval %}) | {% $fig.three_passages_brief %} ({% $fig.three_passages_brief_interval %}) | {% $fig.three_passages_verdict %} |
| `unranked` | {% $fig.unranked_cites_answer %} ({% $fig.unranked_cites_answer_interval %}) | {% $fig.unranked_finished %} ({% $fig.unranked_finished_interval %}) | {% $fig.unranked_brief %} ({% $fig.unranked_brief_interval %}) | {% $fig.unranked_verdict %} |
| `warmer` | {% $fig.warmer_cites_answer %} ({% $fig.warmer_cites_answer_interval %}) | {% $fig.warmer_finished %} ({% $fig.warmer_finished_interval %}) | {% $fig.warmer_brief %} ({% $fig.warmer_brief_interval %}) | {% $fig.warmer_verdict %} |
| planted | {% $fig.planted_cites_answer %} ({% $fig.planted_cites_answer_interval %}) | {% $fig.planted_finished %} ({% $fig.planted_finished_interval %}) | {% $fig.planted_brief %} ({% $fig.planted_brief_interval %}) | {% $fig.planted_verdict %} |

The planted regression, the rerun with the citations taken out of the replies to {% $fig.dropped %} questions, is stopped on `cites_answer`, and the warmer prompt on how its replies end and how long they run. The rerun ships. Gated each at {% $fig.alpha %}, the {% $fig.scores %} scores would stop a release no worse than the baseline up to {% $fig.each_alpha %} of the time; at {% $fig.alpha %} over {% $fig.scores %} each, the chance that any of them stops it is at most {% $fig.alpha %}.

The unranked search ships, though its replies cite the answer less often: its drop is below what this test set can be counted on to find, and its interval reaches above zero. The gate reports it, and a release that drops by less than the test set can find is the help desk's call to make on the interval, with more questions if it matters.

The desk's {% $fig.tasks %} tasks were each run {% $fig.trials %} times by each of the Tools and planning lab's two agents, with a seed of its own for each run: one on the Workflows and agents lab's tools, the first tools below, and one on the tools written for the model in Tools and planning, the new tools:

| k | pass^k, first tools | pass^k, new tools | pass@k, first tools | pass@k, new tools |
| --- | --- | --- | --- | --- |
| 1 | {% $fig.last_every_1 %} | {% $fig.this_every_1 %} | {% $fig.last_every_1 %} | {% $fig.this_every_1 %} |
| 2 | {% $fig.last_every_2 %} | {% $fig.this_every_2 %} | {% $fig.last_some_2 %} | {% $fig.this_some_2 %} |
| 3 | {% $fig.last_every_3 %} | {% $fig.this_every_3 %} | {% $fig.last_some_3 %} | {% $fig.this_some_3 %} |
| 4 | {% $fig.last_every_4 %} | {% $fig.this_every_4 %} | {% $fig.last_some_4 %} | {% $fig.this_some_4 %} |
| 5 | {% $fig.last_every_5 %} | {% $fig.this_every_5 %} | {% $fig.last_some_5 %} | {% $fig.this_some_5 %} |

With one trial, the two are the same number: the share of runs that did their task, {% $fig.last_every_1 %} on the first tools, with a {% $fig.confidence %} interval from {% $fig.last_every_1_interval %}, and {% $fig.this_every_1 %} on the new, from {% $fig.this_every_1_interval %}. They part as k grows. pass@k counts a task done once any of its trials does it, and climbs: on {% $fig.trials %} trials, to {% $fig.last_some_5 %}, from {% $fig.last_some_5_interval %}, and {% $fig.this_some_5 %}, from {% $fig.this_some_5_interval %}. pass^k counts it only when every trial does, and falls, to {% $fig.last_every_5 %}, from {% $fig.last_every_5_interval %}, and {% $fig.this_every_5 %}, from {% $fig.this_every_5_interval %}.

A caller gets one conversation, not several to choose from, and the next caller with the same request gets another. τ-bench's authors proposed pass^k for that reason: "For real-world agent tasks requiring reliability and consistency like customer service, we propose a new metric – pass^k (pass hat k), defined as the chance that all k i.i.d. task trials are successful, averaged across tasks." On one trial, the two agents are close. On {% $fig.trials %}, the new tools did fewer tasks every time: {% $fig.this_always %} of the {% $fig.tasks %}, against {% $fig.last_always %}, while {% $fig.this_never %} and {% $fig.last_never %} were never done at all.

Each task's estimate is worked out from its own trials, and the interval from the spread of the {% $fig.tasks %} tasks' estimates, so each task counts once, however many trials it has.

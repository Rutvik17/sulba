The desk's {% $fig.tasks %} tasks were each run {% $fig.trials %} times with the last lab's agent, on its tools, and {% $fig.trials %} times with this one, with Qwen3.5-4B and the same seed for both agents in each run:

| Tasks | The last lab's tools | This lab's tools | This less the last | Its {% $fig.confidence %} interval |
| --- | --- | --- | --- | --- |
| Questions | {% $fig.question_last %} | {% $fig.question_this %} | {% $fig.question_difference %} | {% $fig.question_interval %} |
| Cases | {% $fig.case_last %} | {% $fig.case_this %} | {% $fig.case_difference %} | {% $fig.case_interval %} |
| Callbacks | {% $fig.callback_last %} | {% $fig.callback_this %} | {% $fig.callback_difference %} | {% $fig.callback_interval %} |
| New callbacks | {% $fig.new_last %} | {% $fig.new_this %} | {% $fig.new_difference %} | {% $fig.new_interval %} |
| Vague callbacks | {% $fig.vague_last %} | {% $fig.vague_this %} | {% $fig.vague_difference %} | {% $fig.vague_interval %} |
| All | {% $fig.all_last %} | {% $fig.all_this %} | {% $fig.all_difference %} | {% $fig.all_interval %} |

As in the last lab, each share is of the runs that did the task, and the difference is worked out task by task, with an interval that counts each task once.

On cases and callbacks, this lab's agent wrote before the caller's yes in {% $fig.this_early %} of its runs, against {% $fig.last_early %} of the last one's. The model has no tool that writes, and the desk writes only in `confirm`, so the rule holds whatever the model does. On questions, {% $fig.this_uncited %} of the runs cited no passage, against {% $fig.last_uncited %}: each passage now comes with the way to cite it. Most of the questions still not done cited passages that don't hold the answer, {% $fig.this_miscited %} of the runs against {% $fig.last_miscited %}. Callbacks for an open ticket did more: on the last lab's tools, the model booked some before the caller's yes, and opened a new ticket for others that already had one.

Cases and new callbacks did less. In {% $fig.this_unmade %} of this agent's runs on cases and callbacks, the caller's yes opened no ticket or booked no callback, against {% $fig.last_unmade %} of the last agent's. In {% $fig.unmade_asked %} of those {% $fig.unmade %} runs, the model proposed nothing before its first reply, which often asked the caller in words instead. The caller's yes came to a desk with nothing pending, so it made nothing, and the proposal the model made after it waited for a yes the caller had already given. In {% $fig.unmade_ticket %} more, the model proposed a new callback's ticket but not its call, and the yes opened the ticket alone. Each task's caller says yes once.

That is the failure a yes in code trades for. When the model gets the order wrong, the desk does less than the caller asked, never more; on the last lab's tools, a model that got the order wrong made a write the caller hadn't agreed to. Over all the tasks, the two agents did about as many, {% $fig.all_difference %}, with an interval from {% $fig.all_interval %}.

This agent's runs took a median of {% $fig.this_seconds %} seconds, against the last one's {% $fig.last_seconds %}, with {% $fig.this_requests %} requests a run on average to its {% $fig.last_requests %}, and {% $fig.this_tokens %} tokens of prompt to its {% $fig.last_tokens %}. A proposal does in one call the lookups the last agent made a request each for.

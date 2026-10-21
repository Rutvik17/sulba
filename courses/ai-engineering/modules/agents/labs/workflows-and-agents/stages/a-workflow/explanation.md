The workflow asks the model for what code can't do, sorting a message and writing an answer from passages, and does the rest itself. Anthropic's guide to building agents describes exactly this pattern, routing: "Routing classifies an input and directs it to a specialized followup task", with the example of "directing different types of customer service queries (general questions, refund requests, technical support) into different downstream processes, prompts, and tools." Each path's prompt does one job, and the schema holds the model to the fields code needs.

The rule that the caller says yes before anything is made lives in code: the offer waits on the workflow, and only a yes in the next message makes it. The model can't skip it, because the model never calls a tool.

The desk's {% $fig.tasks %} tasks were each run {% $fig.trials %} times with the workflow and Qwen3.5-4B on GitHub's runners:

| Tasks | Done | Median seconds a task | Requests a task |
| --- | --- | --- | --- |
| Questions | {% $fig.question_done %} | {% $fig.question_seconds %} | {% $fig.question_requests %} |
| Cases | {% $fig.case_done %} | {% $fig.case_seconds %} | {% $fig.case_requests %} |
| Callbacks | {% $fig.callback_done %} | {% $fig.callback_seconds %} | {% $fig.callback_requests %} |
| New callbacks | {% $fig.new_done %} | {% $fig.new_seconds %} | {% $fig.new_requests %} |
| Vague callbacks | {% $fig.vague_done %} | {% $fig.vague_seconds %} | {% $fig.vague_requests %} |
| All | {% $fig.all_done %} | {% $fig.all_seconds %} | {% $fig.all_requests %} |

Done is the share of runs that did the task, as the desk's state and replies show. A question takes two requests and a search; a ticket or a callback takes one request, and the rest is code.

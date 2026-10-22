The desk's {% $fig.tasks %} tasks were each run {% $fig.agent_trials %} times with the agent and {% $fig.workflow_trials %} times with the workflow, with Qwen3.5-4B and a seed of its own for each run:

| Tasks | Workflow | Agent | Agent less workflow | Its {% $fig.confidence %} interval |
| --- | --- | --- | --- | --- |
| Questions | {% $fig.question_workflow %} | {% $fig.question_agent %} | {% $fig.question_difference %} | {% $fig.question_interval %} |
| Cases | {% $fig.case_workflow %} | {% $fig.case_agent %} | {% $fig.case_difference %} | {% $fig.case_interval %} |
| Callbacks | {% $fig.callback_workflow %} | {% $fig.callback_agent %} | {% $fig.callback_difference %} | {% $fig.callback_interval %} |
| New callbacks | {% $fig.new_workflow %} | {% $fig.new_agent %} | {% $fig.new_difference %} | {% $fig.new_interval %} |
| Vague callbacks | {% $fig.vague_workflow %} | {% $fig.vague_agent %} | {% $fig.vague_difference %} | {% $fig.vague_interval %} |
| All | {% $fig.all_workflow %} | {% $fig.all_agent %} | {% $fig.all_difference %} | {% $fig.all_interval %} |

Each share is of the runs that did the task. The difference is worked out task by task: a task's share of its agent runs less its share of its workflow runs, averaged over the tasks, with an interval from the spread of those differences. A task's runs aren't independent of each other, since a hard task is hard in every run, so the interval counts each task once, through its shares. Counting each run as a task of its own would make it narrower than the evidence allows.

The workflow did more of each kind of task but the vague callbacks, where the agent changed nothing in any run. On questions, {% $fig.uncited %} of the agent's runs cited no passage at all, though its prompt asks it to cite each one it uses. On cases and callbacks, {% $fig.early %} of its runs opened a ticket or booked a callback before the caller said yes. The agent has that rule in its prompt, which the model can skip; the workflow has it in code.

The agent's runs took a median of {% $fig.agent_seconds %} seconds, against the workflow's {% $fig.workflow_seconds %}, with {% $fig.agent_requests %} requests a run on average to the workflow's {% $fig.workflow_requests %}, and {% $fig.agent_tokens %} tokens of prompt to its {% $fig.workflow_tokens %}. Each of the agent's requests sends the whole conversation again, with the desk's tools and every tool result so far, so its prompts grow with every round.

Anthropic's guide to building agents puts the trade this way: "Agentic systems often trade latency and cost for better task performance, and you should consider when this tradeoff makes sense." On the desk's tasks the agent paid the latency and the cost and did fewer of them. What it handles that the workflow can't is a conversation no path foresaw, which is where the desk's router sends it.

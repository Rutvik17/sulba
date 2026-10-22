The router's runs of the desk's tasks, three of each, beside the workflow's and the agent's:

| Tasks | Workflow | Agent | Router |
| --- | --- | --- | --- |
| Questions | {% $fig.question_workflow %} | {% $fig.question_agent %} | {% $fig.question_router %} |
| Cases | {% $fig.case_workflow %} | {% $fig.case_agent %} | {% $fig.case_router %} |
| Callbacks | {% $fig.callback_workflow %} | {% $fig.callback_agent %} | {% $fig.callback_router %} |
| New callbacks | {% $fig.new_workflow %} | {% $fig.new_agent %} | {% $fig.new_router %} |
| Vague callbacks | {% $fig.vague_workflow %} | {% $fig.vague_agent %} | {% $fig.vague_router %} |
| All | {% $fig.all_workflow %} | {% $fig.all_agent %} | {% $fig.all_router %} |

Task by task, the router's share less the workflow's is {% $fig.less_workflow %}, with a {% $fig.confidence %} interval of {% $fig.less_workflow_interval %}, and less the agent's {% $fig.less_agent %}, from {% $fig.less_agent_interval %}. Its median run took {% $fig.router_seconds %} seconds, the workflow's {% $fig.workflow_seconds %} and the agent's {% $fig.agent_seconds %}.

{% $fig.to_agent %} of the router's {% $fig.router_runs %} runs went to the agent, and {% $fig.to_agent_vague %} of those were vague callbacks, opened from the desk's home page with a first message that named no service. The other {% $fig.on_path %} went down the workflow's paths, with the same requests and the same seeds as the workflow's own runs of those tasks, and {% $fig.otherwise %} of them still came out otherwise than the workflow's: the same request doesn't always come back with the same reply. The router's difference from the workflow comes from those runs, so on the desk's tasks it does what the workflow does, at close to its cost.

The agent takes only what has no path: a callback for a service with two open tickets, a message sorted as other, a callback with no service or no day. There the workflow can only ask the caller again, while the agent can look up the caller's tickets and carry the conversation on from there.

Anthropic's guide says routing "works well for complex tasks where there are distinct categories that are better handled separately, and where classification can be handled accurately". The desk's route is that classification, and each conversation is sorted once, by its first message: the workflow holds an offer for the caller's next message, and the agent holds every message and tool result so far, so sorting a later message again would drop them.

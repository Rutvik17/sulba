Each question the desk answers leaves its search in the conversation: five passages, read once. A researcher keeps them out. Anthropic's guide to context engineering describes sub-agents that each "might explore extensively, using tens of thousands of tokens or more, but returns only a condensed, distilled summary of its work (often 1,000-2,000 tokens)." The desk's researchers work the same way at its scale. Each searches one service's help pages in a conversation of its own, and gives the agent a short answer with the passages it cites.

In `researchers.py`, write:

- `Researcher.answer(question)`, which starts a conversation for the question with the researcher's system prompt, `RESEARCHER` with the service's name, and offers `SEARCH` as its one tool, whose calls `run` runs with `search(query, service)`. It takes at most `rounds` requests, each with `MODEL`, `SAMPLING` and `max_tokens`, the last of them without tools, so that the model answers, and gives the model's answer.
- `Researchers.research(service, question)`, the answer of the service's researcher. When there's no researcher for the service, it gives an error that names the services there are; when the answer is empty, `"The researcher found no answer."`.
- `Researchers.call(name, arguments)`, which runs the agent's call of `research` from its arguments as JSON text. When they aren't a service and a question, it gives an error that shows a call that works.

`tool()` is given: `research`, as the agent's tools give it. `ASK` is the desk's system prompt's line on questions, for `research` in place of `search_help`.

```
Researchers(client, search, services, rounds=3, max_tokens=300)
```

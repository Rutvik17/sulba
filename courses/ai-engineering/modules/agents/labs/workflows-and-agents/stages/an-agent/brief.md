In an agent, the model decides what happens next. It reads the conversation and the desk's tools, calls the tools it needs for as long as it needs them, and then replies to the caller. The desk's agent keeps the workflow's rules in its system prompt, `SYSTEM`, followed by a blank line and the pages the chat was opened from: `f"The caller opened the chat on the {SERVICES[page]} pages."`, or `"The caller opened the chat on the help desk's home page."`

In `agent.py`, write `Agent.reply(message)`, the desk's reply to the caller's next message. It sets the desk's `turn` to the number of messages before it, from 0, adds the message to the conversation, and sends the whole conversation with the desk's tools, `tools()`, the agent's `max_tokens` and the model's `SAMPLING`. When the model's reply calls tools, each call runs, in order, through the desk's `call`, and each result goes back after the model's message, in a message with the role `tool` and the call's id; then the agent asks again. A reply that calls no tools is the reply to the caller. Every message, the model's and the tools', stays in `messages`, so the next turn goes on from there.

A turn takes at most `rounds` requests: when the model still calls tools after them, `reply` raises `OutOfRounds`. Keep each request in `requests`, as a `Request`: its tokens of prompt and of reply, from the response's `usage`, the seconds it took, why the reply finished, and the names of the tools it called.

```
Agent(client, desk, page, rounds=8, max_tokens=768).reply(message) -> str
```

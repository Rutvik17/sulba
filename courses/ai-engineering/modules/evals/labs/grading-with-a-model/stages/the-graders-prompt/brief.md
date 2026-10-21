The help desk's checks in code can't tell whether what a reply says is in the passages it was given. It will ask Granite Guardian 3.1 2B, a model IBM trained to judge whether an assistant's message keeps to its context. `uv run sulba.py model` serves it on your machine as `Granite-Guardian-3.1-2B`. It answers one question, in one word, `Yes` when the message says something the context doesn't, and `No` when it doesn't, and it was trained on that question in the words of its chat template, which IBM ships in `data/tokenizer_config.json`. llama.cpp's server can't run this template on its chat endpoint, so the code renders the prompt itself and sends it to the completions endpoint.

In `grader.py`, write:

- `template(path)`: the `chat_template` in a tokenizer's configuration, compiled as transformers compiles one: in jinja2's `ImmutableSandboxedEnvironment` with `trim_blocks` and `lstrip_blocks` on and the `jinja2.ext.loopcontrols` extension, with a `raise_exception` function that raises `jinja2.TemplateError` with its message.
- `prompt(chat, context, reply, today)`: the template rendered with two messages, the context with the role `context` and the reply with the role `assistant`; `guardian_config` naming the risk `groundedness`; the prompt for the answer added; and `strftime_now`, which the template calls for today's date, giving `today`.
- `risk(client, prompt)`: the probability the grader gives `Yes`. Post the prompt to `/completions` for the model `Granite-Guardian-3.1-2B`, with `max_tokens` 1, `temperature` 0 and `logprobs` {% $fig.likeliest %}, for the {% $fig.likeliest %} likeliest first tokens. As IBM's model card reads them, a token is `Yes` or `No` when it is one with the spaces around it taken off, in any case. Sum each one's probabilities, and give `Yes`'s share of the two. A request the server refuses raises.

`client` is an `httpx.Client` whose base URL is the server's API. The tests compare your prompts with the ones transformers renders from IBM's tokenizer.

```
template(path) -> jinja2.Template
prompt(chat, context, reply, today) -> str
risk(client, prompt) -> float
```

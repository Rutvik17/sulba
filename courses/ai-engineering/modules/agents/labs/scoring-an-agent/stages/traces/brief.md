Scores and percentiles need each run's seconds, tokens and errors, and in production they come from traces: a span for each piece of a run's work, timed, with attributes that say what it was. OpenTelemetry's semantic conventions for generative AI name the spans and their attributes, so that any tracing backend can read an agent's traces.

In `traces.py`, write:

- `Traced(client, tracer)`, whose `post(url, json=body)` sends a chat request through the client in a span named `chat {model}`, of kind `CLIENT`, and returns the response. The span's attributes:
  - From the request: `gen_ai.operation.name`, `"chat"`; `gen_ai.provider.name`, `PROVIDER`; `gen_ai.request.model`, the body's model; `server.address` and `server.port`, the host and port of the client's `base_url`, the port 80 for `http` and 443 for `https` when the URL gives none; and `gen_ai.request.max_tokens`, `gen_ai.request.temperature`, `gen_ai.request.top_p`, `gen_ai.request.top_k`, `gen_ai.request.presence_penalty` and `gen_ai.request.seed`, each the body's setting of that name, when it has one.
  - From a reply: `gen_ai.response.id` and `gen_ai.response.model`, its id and model; `gen_ai.response.finish_reasons`, the finish reason of each choice; and `gen_ai.usage.input_tokens` and `gen_ai.usage.output_tokens`, its usage's tokens of prompt and of reply.
  - From an error status: `error.type`, the status code as text, such as `"503"`, and the span's status `ERROR`.
  - From an httpx error the request raises: `error.type`, the exception's class name, such as `"RemoteProtocolError"`. The error goes on to the caller.
- `tool(tracer, call)`, which gives `call(name, arguments)`, each call of it in a span named `execute_tool {name}`, of kind `INTERNAL`, with `gen_ai.operation.name` `"execute_tool"`, `gen_ai.tool.name` the name and `gen_ai.tool.type` `"function"`.
- `agent(tracer, name, model)`, a context manager that gives a span named `invoke_agent {name}`, of kind `INTERNAL`, current while it lasts, with `gen_ai.operation.name` `"invoke_agent"`, `gen_ai.provider.name` `PROVIDER`, `gen_ai.agent.name` the name and `gen_ai.request.model` the model.
- `runs(spans)`, from finished spans, a row for each trace whose root span, the one with no parent, is an agent's, in the order the roots began. A row has `seconds`, the root's, to three places; `requests`, the trace's chat spans; `prompt_tokens` and `completion_tokens`, their tokens; `tools`, the trace's tool spans; and `error`, the root's `error.type`, or `""`. Each value is text, as in `runs.csv`.

An exception raised in a tool or an agent's span sets the span's `error.type` to its class name, and goes on.

```
Traced(client, tracer).post(url, json=body) -> httpx.Response
tool(tracer, call) -> Callable[[str, str], str]
agent(tracer, name, model) -> context manager of Span
runs(spans) -> list[dict[str, str]]
```

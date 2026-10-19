# 31. Test a lab's model calls against a scripted model

- Status: accepted
- Date: 2026-10-19

## Context

Intermediate's Building on model APIs module teaches code that calls a model over HTTP: chat requests, streamed replies, tool calls, structured output and retries. Its labs run on the learner's machine (record 28), where a real model can run, but a stage's tests and checks must give the same result on every machine, and the runner's fixtures the same result in Pyodide and CPython (record 17). A real model's words differ from one machine to the next. In a spike on six of GitHub's runners, llama.cpp's llama-server with Qwen3.5-0.8B, the model the module runs, wrote three different replies to the same request at temperature 0. And a test of what code does with a slow reply, a rate limit or a dropped connection needs the server to misbehave when the test says.

## Decision

- **The `model` fixture:** a scripted model server, in `sulba_fixtures.py` with the runner's other fixtures. A test scripts its replies in order, such as `model.says("We open at 9.")`, and code reaches it through httpx. `model.client()` and `model.async_client()` give clients whose base URL is the model's API, `http://model.test/v1`, over httpx's `MockTransport`, and the openai package takes either as its `http_client`.
- **What it serves:** `POST /v1/chat/completions`, in the form llama-server b11734 gives it. When the request asks to stream, the same reply comes as server-sent events, with its text and each tool call's arguments in the pieces the test gives, and a last chunk with the tokens used when the request asks for one. Replies and tool calls have ids numbered in order. It refuses what llama-server refuses, with the same status and words, and answers any other path with 404.
- **Failures on cue:** `model.fails(429, "...", retry_after=2)` answers with an error in llama-server's form, a reply can take `after` seconds, `model.hangs()` never answers, and `model.disconnects()` drops the connection. Time passes on the `loop` fixture's clock (record 21): a client whose read timeout is shorter than a reply's wait raises `httpx.ReadTimeout` when the timeout ends. A sync client waits for nothing, but raises it all the same.
- **Replies from a function:** `model.answers(function)` scripts the answer to each request the test scripted none for, from the request, so a test can play a model that obeys every instruction it reads.
- **Running out:** a request with no reply scripted raises `NoReplyLeft`, which isn't an `Exception`, so code that handles errors can't hide it, and the test fails with the request's number.
- **What was sent:** `model.requests` keeps every request's method, path, headers and JSON body, for tests to check.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A scripted model over httpx's `MockTransport`, as a fixture (chosen) | The same result on every machine, in Pyodide and CPython; failures on cue; no download | Code takes its client from the test, so code that opens its own connection, through urllib or requests, can't reach it |
| The real model: llama-server with Qwen3.5-0.8B | The model the learner calls | Its words differ between machines, and between a streamed reply and the same reply whole; 834 MB and a running server before any test; it can't fail on cue |
| A scripted server on a local port, in a thread or a process | Any HTTP client reaches it | Pyodide has neither sockets nor threads, so the fixtures couldn't run in both runtimes, and a port can be taken |
| Replies recorded from a real model and replayed | Real replies | A learner's request differs from the recorded one in ways that don't matter, so it misses, and a recording goes stale with the model |
| Patching the openai package's methods | Short tests | Tests only code written with that package, and nothing of what goes over HTTP |

## Evidence

- The spike sent the same requests at temperature 0 to llama.cpp b11734's CPU builds with ggml-org's Qwen3.5-0.8B Q8_0, at revision 8fea620, on GitHub's ubuntu-24.04, ubuntu-24.04-arm, windows-2025, windows-11-arm, macos-15 and macos-15-intel runners. Each system gave the same reply twice, but the six systems gave three different replies. A streamed reply differed from the same request's whole reply on five of the six. A reply held to a JSON schema ran to its 200-token limit, as invalid JSON, on five, and finished on the sixth. All six called the same tool with the same arguments.
- llama-server's [README at b11734](https://github.com/ggml-org/llama.cpp/blob/b11734/tools/server/README.md), on `cache_prompt`, which is on by default: "the logits are **not** guaranteed to be bit-for-bit identical for different batch sizes (prompt processing vs. token generation) enabling this option can cause nondeterministic results."
- llama.cpp b11734's server source. `format_error_response` in [`server-common.cpp`](https://github.com/ggml-org/llama.cpp/blob/b11734/tools/server/server-common.cpp) gives an error its status, message and a type, such as `invalid_request_error` for 400 and `unavailable_error` for 503, and `oaicompat_chat_params_parse` there refuses a body without `messages`, with `messages` not an array, or with a message without its content. In [`server-task.cpp`](https://github.com/ggml-org/llama.cpp/blob/b11734/tools/server/server-task.cpp), a stream sends the role, then each piece of text and of each tool call, then why the reply finished, and, when the request asks for usage, "an empty `choices` array for the last chunk".
- httpx's [Transports](https://www.python-httpx.org/advanced/transports/#mock-transports): "The httpx.MockTransport class accepts a handler function, which can be used to map requests onto pre-determined responses". Its [Timeouts](https://www.python-httpx.org/advanced/timeouts/): "The default behavior is to raise a TimeoutException after 5 seconds of network inactivity", and "If HTTPX is unable to receive data within this time frame, a ReadTimeout exception is raised."
- The openai package 2.30.0, Pyodide's: `ChatCompletionChunk` says `usage` is there only when the request sets `stream_options: {"include_usage": true}`, with `choices` empty in that last chunk. The `uses-model` fixture shows the package reading the scripted model's whole and streamed replies, putting two streamed tool calls back together with `chat.completions.stream`, and raising `RateLimitError` for a 429, with the same results in Pyodide and CPython.

## Why

A scripted model is the only option whose result is the same on every machine, and the only one that fails when a test asks it to, which is what a client's error handling needs. httpx's `MockTransport` needs no socket or thread, so the fixture runs in Pyodide and CPython alike, and a test of time runs on the loop's virtual clock, as asyncio tests already do. Taking the replies, refusals and errors from llama-server's source keeps code that passes against the script working against the model the learner runs. The strongest case against: code that passes against a script has never met a real model's mistakes, such as a reply cut off at its limit or a tool call whose arguments don't parse. The labs script those mistakes, and the learner runs their code against the real model too.

## Consequences

A lab's code takes its httpx client from its caller, as code that's easy to test does anyway, and a stage that teaches urllib or requests can't use the fixture. No number a learner sees comes from a run of the real model: it comes from scripted replies or published figures. The fixture serves chat completions only, so an endpoint such as embeddings joins it when a lab needs one. A reply's `created` is 0, and its usage is what the test scripts, 0 by default.

## Revisit when

A lab needs an endpoint other than chat completions, or llama-server changes the form of its replies in a build the labs pin.

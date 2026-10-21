# 36. Let a lab give its chat model a longer context

- Status: accepted
- Date: 2026-10-21
- Amends: [34. Serve a lab's models on the learner's machine with llama.cpp's server](0034-serve-a-labs-models-with-llama-cpps-server.md)

## Context

Record 34 runs every chat model with a context of 4,096 tokens, which a question with five passages and its reply fits. An agent's conversation is longer: the system prompt and the tools' descriptions, the caller's messages, and each tool's result, a search's five passages of up to 200 words each among them, all go back to the model on every request. The context is also memory: the server holds a key and a value for every token of it, for each attention layer, as long as it runs, beside the weights, on a learner's machine that the Intermediate level asks to have 8 GB.

## Decision

- An entry in `models` in `lab.yaml` whose kind is `chat` can give a `context`: the tokens of conversation the server reads, a multiple of 1,024 from 4,096 to 32,768. The runner writes it as the model's `ctx-size` in the server's preset file. A chat model without one keeps record 34's 4,096, and an embedding model or a reranker can't take one.
- The content check refuses a `context` outside that range, not a multiple of 1,024, or on a model of another kind. The download's `lab.json` carries it to the runner.
- Everything else record 34 sets stands.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A `context` a lab can give its chat model (chosen) | Each lab pays in memory only for the conversations it has; the labs that serve two chat models at once keep record 34's 4,096 | One more field in `lab.yaml`, and one more check |
| A longer context for every chat model | No field to set | Every lab's chat models hold the memory of the longest conversation any lab has, the Evals labs' two at once among them |
| Keep 4,096, and have each lab's code keep its conversations short | No change to the runner | An agent's search results alone take a large part of it, and a learner running their own code against the real model meets a server that refuses the request |

## Evidence

- llama-server b11734, as `sulba.py` pins it, serving Qwen3.5-4B at 4 bits (unsloth's Q4_K_M GGUF, 2,740,937,888 bytes) with one slot and reasoning off, in a 4-CPU Linux container on 2026-10-21, once loaded: 4,201 MB resident with a context of 4,096 tokens, 4,585 MB with 16,384 and 5,097 MB with 32,768.
- In a trial of a help desk's agent on 2026-10-21, with llama-server b11734 on GitHub's Ubuntu runners, 40 tasks run twice each with a search tool that gives five passages: the first request of each conversation, the system prompt and five tools' descriptions with the caller's message, took 914 to 916 tokens. Qwen3.5-2B's requests reached 6,805 tokens of prompt and reply, three of 171 more than 4,096; Qwen3.5-4B's reached 2,787, and with thinking on, 3,511.
- [llama.cpp's server README at b11734](https://github.com/ggml-org/llama.cpp/blob/b11734/tools/server/README.md) gives `-c, --ctx-size N` as "size of the prompt context", which the preset's `ctx-size` sets, and calls a reply `truncated` when "the number of tokens provided in the prompt (`tokens_evaluated`) plus tokens generated (`tokens predicted`) exceeded the context size (`n_ctx`)". The same server, with Qwen3.5-4B and a context of 4,096, answered a prompt of 4,916 tokens with `400` and "request (4916 tokens) exceeds the available context size (4096 tokens), try increasing it".

## Why

A context is memory held for as long as the server runs, so it belongs with the lab that needs it, as a lab's models and data do. Agents' conversations grow with every tool's result, and an agent's lab teaches keeping them within a budget, which the code does; the server's context only has to hold what that budget allows. The strongest case against: a learner whose machine has less memory free than the lab assumes meets a model that won't load, where record 34's 4,096 would have loaded. The level states the memory it needs, and a lab that sets a context counts it there.

## Consequences

A lab that sets a `context` raises what its models hold in memory, and the level's `needs` in `course.yaml` has to allow for it. `pnpm check:machine --model` loads each model with the context its lab gives, on Windows, macOS and Linux.

## Revisit when

A lab needs a conversation longer than 32,768 tokens, or llama-server can grow a context as a conversation needs it.

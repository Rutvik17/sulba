# 34. Serve a lab's models on the learner's machine with llama.cpp's server

- Status: accepted
- Date: 2026-10-20
- Supersedes: [32. Run a lab's model on the learner's machine with llama.cpp's server](0032-run-a-labs-model-with-llama-cpps-server.md)

## Context

Record 32 serves one chat model for a lab, with llama.cpp's llama-server. The Retrieval module's labs need three at once: an embedding model that turns passages and questions into vectors, a reranker that scores passages for a question, and a chat model that answers from the passages found. Their tests call scripted models (record 31), but a learner's own code should meet real ones. Sulba runs no model (record 17), so they run on the learner's machine, from the lab's download (record 28), on every system the Intermediate level supports, often without a GPU. They have to cost nothing and be pinned like every other file a lab fetches (record 29).

## Decision

- **The command:** `uv run sulba.py model`, in the download of a lab whose `lab.yaml` lists `models`, starts them all in one llama-server, in its router mode. They answer at `http://127.0.0.1:9931/v1` until Ctrl+C stops it, each to the requests that give its title as `model`. The runner says they answer once the server has loaded every one. `--port` takes another port. `--check` asks each model one thing, as its kind allows, shows the answer and stops, for CI and for a learner to see that they work.
- **The models:** each entry in `models` gives a title, a kind (`chat`, `embedding` or `reranking`), the credit its licence asks for, and one GGUF file, pinned by size and sha256 and fetched from its publisher as a fetched file is. A title has only letters, digits, dots, dashes and _, and each model in a lab has a title of its own. The Building on model APIs labs serve record 32's Qwen3.5-0.8B at 8 bits. A Retrieval lab serves the ones it uses of that model, nomic-embed-text-v1.5 at 8 bits, from Nomic AI's GGUF repository at revision 0188c9b, 146,146,432 bytes, and Qwen3-Reranker-0.6B at 8 bits, from ggml-org's GGUF repository at revision a02f48b, 639,153,184 bytes, both under the Apache License 2.0.
- **How each kind runs:** the runner writes the server a preset file, with a section for each model, named by its title and loaded as the server starts. A chat model has a context of 4,096 tokens and reasoning off, as record 32 set. An embedding model has a context of 2,048 tokens and batches of 2,048, so it embeds a text of up to 2,048 tokens in one pass. A reranker has a context of 4,096 tokens and batches of 2,048, so it scores a query and a passage of up to 2,048 tokens together. Where a model was trained on fewer tokens, the server holds its requests to those. On macOS, a chat model runs on the GPU, through Metal, and an embedding model or a reranker on the CPU.
- **The server:** the CPU build of llama.cpp's release b11734 for the learner's system, from llama.cpp's GitHub releases, pinned in `sulba.py` by size and sha256 for Windows x64 and ARM64, macOS on Apple silicon and Intel, and Linux x64 and ARM64, as record 32 set. It runs in the cache folder, and the preset names each model's file from there.
- **One copy for every lab:** the server and the models are fetched into `sulba` in the learner's cache folder, `~/.cache`, or `$XDG_CACHE_HOME` where it's set, the first time a learner runs the command, and never before a lab's tests, which don't need them.
- **When it can't start:** the runner says why. The reasons are no build for the system, a port in use, on Windows the Visual C++ runtime missing, with the address of Microsoft's installer, and a model the server couldn't load, with the end of what the server wrote.
- **CI:** on every run, the Models jobs run `uv run sulba.py model --check` on Windows, macOS and Linux, from the download of each lab that serves a model no lab before it serves. The content package's fixture lab serves a small model of each kind.

## Options

How to serve several models:

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| One llama-server in router mode, with a preset file (chosen) | One address for every model, each reached by its name, as a provider's API names a model; the router runs each model in a process of its own and passes each request to the one it names; a model that fails to load fails alone | A request has to name its model; every model holds its memory while the server runs |
| A llama-server for each model, each at a port of its own | Each server runs as record 32 runs one | An address for each model, which the learner's code has to keep apart; the runner starts, watches and stops several servers |

Which embedding model:

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| nomic-embed-text-v1.5 at 8 bits (chosen) | 146 MB; on MultiDoc2Dial, the higher recall at 1 and the same at 5; embedded 425 to 988 tokens a second on the spike's runners; ran on Metal on macOS 14 | A context of 2,048 tokens in llama.cpp, a quarter of the model's 8,192; its prefixes, `search_query:` and `search_document:`, are the caller's to add; lower recall at 10, 20 and 50 |
| Qwen3-Embedding-0.6B at 8 bits | Higher recall at 10, 20 and 50; a context of 32,768 tokens | 639 MB; embedded 113 to 315 tokens a second; on macOS 14, llama-server stopped at an assertion in its Metal code as it loaded the model |

Which reranker:

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Qwen3-Reranker-0.6B at 8 bits (chosen) | Ranked every spike question's answer first on every runner it ran on | 639 MB; scored 8 passages in 4.2 to 15.0 seconds on the runners |
| jina-reranker-v1-turbo-en | 77 MB; scored 8 passages in 0.27 to 0.58 seconds | Ranked the answer sixth of eight for two of the six questions on every runner it ran on, with every score between -0.0877 and -0.0455; on macOS 14, llama-server stopped at the same Metal assertion |

## Evidence

- The spike ran llama-server b11734 on five of GitHub's runners: Linux on x86-64 and on Arm, macOS 14 and 15 on Apple silicon, and Windows Server 2025. Each embedding model embedded 64 passages and six questions, and each question's own passage came first for both models on every runner that ran them. nomic-embed-text-v1.5 embedded 425.0 to 987.9 tokens a second, and Qwen3-Embedding-0.6B 112.8 to 315.3. Qwen3-Reranker-0.6B scored each question against eight passages and ranked its answer first on every runner it ran on, in 4.2 to 15.0 seconds a question. jina-reranker-v1-turbo-en took 0.27 to 0.58 seconds and ranked the answer sixth for two of the questions, its scores within 0.0001 between runners.
- On macOS 14, llama-server stopped as it loaded Qwen3-Embedding-0.6B and jina-reranker-v1-turbo-en on Metal: `GGML_ASSERT(buf_dst) failed` at `ggml-metal-context.m:380`. Run on the CPU, with `--device none`, Qwen3-Embedding-0.6B embedded 315.3 tokens a second there. Qwen3-Reranker-0.6B scored eight passages in 4.2 to 4.9 seconds on the CPU against 8.7 to 9.4 on Metal on macOS 14, and in 4.5 to 6.0 against 9.2 to 9.8 on macOS 15. nomic-embed-text-v1.5 ran on Metal on both, at 646.4 and 618.3 tokens a second.
- One llama-server in router mode, started with a preset of Qwen3.5-0.8B, nomic-embed-text-v1.5 and Qwen3-Reranker-0.6B, the last two with `device = none` on macOS, answered on all five runners: a chat request, embeddings and a rerank, each to the model the request named. It listed the three models at `/v1/models`, embedded a text of 1,989 tokens, which took 2.76 and 2.81 seconds on the CPU on the macOS runners, and scored a question's answer 0.9996, first of eight. A chat request that named no model got `400` and "model name is missing from the request". A model loaded at the first request to it, which took up to 45.6 seconds, on macOS 14.
- On the opening question of each of [MultiDoc2Dial](https://github.com/IBM/multidoc2dial)'s 661 validation dialogues, against the dataset's documents in 2,419 passages of a median 182 words, a passage counting as relevant when it holds at least half of a span of the page that the question itself is grounded in, run in a 4-CPU container through llama-server, with nomic-embed-text-v1.5's prefixes, and Qwen3-Embedding-0.6B's queries written as `Instruct: <task>` and `Query:<question>` on two lines, the task being "Given a web search query, retrieve relevant passages that answer the query":

  | Method | Recall at 1 | at 5 | at 10 | at 20 | at 50 |
  | --- | --- | --- | --- | --- | --- |
  | BM25 | 0.284 | 0.599 | 0.700 | 0.776 | 0.838 |
  | nomic-embed-text-v1.5 | 0.392 | 0.681 | 0.764 | 0.826 | 0.900 |
  | Qwen3-Embedding-0.6B | 0.359 | 0.678 | 0.781 | 0.862 | 0.927 |
  | BM25 and nomic-embed-text-v1.5, by reciprocal rank fusion | 0.360 | 0.682 | 0.779 | 0.859 | 0.932 |
  | BM25 and Qwen3-Embedding-0.6B, by reciprocal rank fusion | 0.357 | 0.693 | 0.803 | 0.865 | 0.935 |

- In that container, the runner's `model --check`, with llama-server b11734 and the fixture lab's three models, stories260K, bge-small-en-v1.5 and jina-reranker-v1-tiny-en, loaded all three as the server started and answered each kind of request in 20 seconds in all. The server's log gave each model's context per request as the smaller of the preset's and the model's own: 512 tokens for bge-small-en-v1.5, which was trained on 512, against the preset's 2,048.
- [llama-server's README at b11734](https://github.com/ggml-org/llama.cpp/blob/b11734/tools/server/README.md), under "Using multiple models": "`llama-server` can be launched in a **router mode** that exposes an API for dynamically loading and unloading models. The main process (the "router") automatically forwards each request to the appropriate model instance." Of presets: "Each section in the file defines a new preset. Keys within a section correspond to command-line arguments (without leading dashes)", and `load-on-startup` "Controls whether the model loads automatically when the server starts". "For **POST** endpoints (`/v1/chat/completions`, `/v1/completions`, `/infill`, etc.) The router uses the `"model"` field in the JSON body", and `--models-max N` is the "maximum number of models to load simultaneously (default: 4, 0 = unlimited)". `GET /models` gives each model's status, `loading`, `loaded`, or `unloaded` with `"failed": true` and its exit code.
- [llama.cpp's preset parser at b11734](https://github.com/ggml-org/llama.cpp/blob/b11734/common/preset.cpp) ends a value at `;` or `#`, which begin a comment, and has no quoting, so a path with either can't be written in a preset. [Its router](https://github.com/ggml-org/llama.cpp/blob/b11734/tools/server/server-models.cpp) starts each model's server as a child process, in the folder the router runs in, and the child stops when its input closes: "EOF detected, that means the router server is unexpectedly exit or killed".
- [nomic-embed-text-v1.5's GGUF README at 0188c9b](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/blob/0188c9bf409793f810680a5a431e7b899c46104c/README.md), under the Apache License 2.0: "Embedding text with `nomic-embed-text` requires task instruction prefixes at the beginning of each string", and "llama.cpp will default to 2048 tokens of context with these files." The file's metadata gives a context of 2,048 and mean pooling.
- [Qwen3-Reranker-0.6B's model card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B), under the Apache License 2.0: "Context Length: 32k". [ggml-org's GGUF of it at a02f48b](https://huggingface.co/ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF/blob/a02f48bb4f057028298c21fa033da2b30d7742d5/README.md) "was converted to GGUF format from `Qwen/Qwen3-Reranker-0.6B` using llama.cpp". Its metadata gives rank pooling over the labels `yes` and `no`, and a chat template that puts each query and document into the card's prompt, with its default instruction.

## Why

Router mode gives the learner's code one address, where each request names its model, as it does with a provider's API, and leaves the runner one server to start and stop. Loading every model as the server starts means the runner says they answer only once they do, so a learner's first request doesn't wait for a load. nomic-embed-text-v1.5 has the higher recall at 1 on the module's own data and the same at 5, is a quarter of Qwen3-Embedding-0.6B's size, and embeds about four times as fast on each runner, which counts when a lab embeds every passage on a laptop's CPU. Qwen3-Embedding-0.6B finds more of the answers in its top 10 to 50, but fused with BM25, as hybrid search fuses them, nomic-embed-text-v1.5's recall at 20 is 0.859 to its 0.865. Qwen3-Reranker-0.6B is the only reranker that put each answer first. The embedding model and the reranker run on the CPU on macOS because Metal stopped two of the four models on macOS 14, and the reranker ran twice as fast on the CPU of both macOS runners. The strongest case against: a Retrieval lab that serves all three models takes 1.6 GB to fetch, and as much memory while the server runs, with no smaller choice in the lab. And the macOS evidence comes from GitHub's virtual machines, whose GPU isn't a Mac's own, so on a Mac Metal may well be faster for the reranker.

## Consequences

A Retrieval lab that serves all three models fetches about 1.6 GB the first time, 785 MB of it beyond the Building on model APIs labs' model, and the server holds the three in memory while it runs. A request that names no model, which record 32's server answered, now gets a `400`; the Building on model APIs labs' code names its model already. The Models jobs fetch each checked lab's models on each system on every run. A lab's tests and checks still call scripted models (record 31). A lab's page credits each model and says how much the command fetches and from where, and the Privacy Policy says that the runner fetches from GitHub and Hugging Face when asked.

## Revisit when

llama.cpp's Metal code runs embedding models and rerankers on macOS 14 and does so faster than the CPU, a lab needs a model the router can't run, a smaller reranker ranks as well as Qwen3-Reranker-0.6B, or llama.cpp signs its Windows builds or ships their runtime with them.

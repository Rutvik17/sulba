# 32. Run a lab's model on the learner's machine with llama.cpp's server

- Status: superseded by [34. Serve a lab's models on the learner's machine with llama.cpp's server](0034-serve-a-labs-models-with-llama-cpps-server.md)
- Date: 2026-10-19

## Context

The Building on model APIs labs teach code that calls a model through the chat completions API that OpenAI and others serve. Their tests call a scripted model (record 31), but a learner's code should meet a real model too. Sulba runs no model (record 17), and a provider's API needs an account, a key and money. So the model runs on the learner's machine, from the lab's download (record 28): on Windows, macOS or Linux, on x64 or ARM, often without a GPU. It has to cost nothing, be pinned like every other file a lab fetches (record 29), and serve the API a provider serves.

## Decision

- **The command:** `uv run sulba.py model`, in the download of a lab whose `lab.yaml` names a `model`, starts that model in llama.cpp's llama-server. The model answers at `http://127.0.0.1:9931/v1` until Ctrl+C stops it. `--port` takes another port. `--check` sends one chat request, shows the reply and stops, for CI and for a learner to see that it works.
- **The server:** the CPU build of llama.cpp's release b11734 for the learner's system, from llama.cpp's GitHub releases. There are builds for Windows x64 and ARM64, macOS on Apple silicon and Intel, and Linux x64 and ARM64, each pinned in `sulba.py` by size and sha256. On Apple silicon the build runs the model on the GPU, through Metal.
- **The model:** `model` in `lab.yaml` names one GGUF file, pinned by size and sha256, with the credit its licence asks for, fetched from its publisher as a fetched file is. The module's labs name Qwen3.5-0.8B at 8 bits, from ggml-org's GGUF repository at revision 8fea620: 833,592,096 bytes, under the Apache License 2.0.
- **One copy for every lab:** both are fetched into `sulba` in the learner's cache folder, `~/.cache`, or `$XDG_CACHE_HOME` where it's set, as Hugging Face places its cache. The fetch happens the first time a learner runs the command, never before a lab's tests, which don't need it.
- **How it runs:** with a context of 4,096 tokens and reasoning off. The server then reads a conversation as the model's own template writes it by default, with no thinking, and the prompt tokens it reports are that template's.
- **When it can't start:** the runner says why. The reasons are no build for the system, a port in use, or on Windows the Visual C++ runtime missing, with the address of Microsoft's installer, or the system refusing to run the server.
- **CI:** on every run, the Models jobs run `uv run sulba.py model --check` on Windows, macOS and Linux, in a download of the first lab that names each model.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| llama.cpp's llama-server from its release builds (chosen) | Chat completions with streaming, tool calls and replies held to a JSON schema; 12 to 20 MB to fetch on each of the six systems; the build and the model each pinned by sha256; MIT | Its Windows builds are unsigned, and need Microsoft's Visual C++ runtime |
| Ollama | The same API; MIT | Between 0.2 and 1.6 GB to install on each system; models are pulled by a tag that can move, with no sha256 to pin them by unless the GGUF is imported |
| llamafile | One file that runs on most systems | No build for Windows on ARM; Windows runs a file only under 4 GB; its release 0.10.6 runs llama.cpp b10441, 1,293 builds before b11734 |
| Llama, the app from llama.cpp's team and Hugging Face | An app for Mac and Windows, and a command line for Linux, that serves the same API at port 9931 | Its install scripts fetch whichever build its `latest` pointer names, and check no checksum or signature |
| transformers in Python, behind a FastAPI app the lab ships | Python packages only | 4.2 tokens a second where llama-server wrote 14.1 on the same machine; streaming, tool calls and replies held to a schema would be Sulba's own code |
| A provider's API | The models learners use at work | It costs money and needs an account and a key, and the learner's prompts leave their machine |

## Evidence

- The spike of record 31 ran the pinned build and model on six of GitHub's runners: Windows x64 and ARM64, macOS on Apple silicon and Intel, and Linux x64 and ARM64. The server was ready in 1.5 to 3.9 seconds on five of them and in 24.9 on the Apple silicon runner, and wrote between 4.0 and 60.7 tokens a second. Every system answered a tool call with the right arguments and held a reply to a JSON schema.
- In a 4-CPU container, llama-server wrote 14.1 tokens a second with Qwen3.5-0.8B at 8 bits, and transformers 5.18 in float32 wrote 4.2.
- With `--reasoning off`, llama-server counted the prompts of two conversations as 19 and 63 tokens, the same as transformers' `apply_chat_template` with the model's template. With its default, `auto`, it counted 17 and 61, from the template's thinking prompt.
- [llama-server's README at b11734](https://github.com/ggml-org/llama.cpp/blob/b11734/tools/server/README.md): `--port` "(default: 9931)", `--host` "(default: 127.0.0.1)", and `--reasoning` "default: 'auto' (detect from template)". For chat completions, "Both synchronous and streaming mode are supported", and `response_format` "supports both plain JSON output … and schema-constrained JSON". [llama.cpp's build docs](https://github.com/ggml-org/llama.cpp/blob/b11734/docs/build.md): "On MacOS, Metal is enabled by default".
- [Qwen3.5-0.8B's model card](https://huggingface.co/Qwen/Qwen3.5-0.8B), under the Apache License 2.0: "Qwen3.5-0.8B operates in non-thinking mode by default", and "Qwen3.5-0.8B is more prone to entering thinking loops compared to other Qwen3.5 models".
- The b11734 Windows builds: `Get-AuthenticodeSignature` reports `NotSigned` for both, and their import tables list `MSVCP140.dll` and `VCRUNTIME140.dll`, and on x64 `VCRUNTIME140_1.dll`, which the zips don't hold.
- Microsoft's [Smart App Control FAQ](https://support.microsoft.com/en-us/windows/security/threat-malware-protection/smart-app-control-frequently-asked-questions): "If the app is unsigned, or the signature is invalid, Smart App Control will consider it untrusted and block it for your protection", and "There is currently no way to bypass Smart App Control protection for individual apps."
- Microsoft's [latest supported Visual C++ Redistributable downloads](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) give `https://aka.ms/vc14/vc_redist.x64.exe` and `https://aka.ms/vc14/vc_redist.arm64.exe`, and say "Redistribution is permitted only for licensed Visual Studio users". [Redistributing Visual C++ Files](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files), on putting the DLLs beside a program: "For servicing reasons, we don't recommend that you use this installation location."
- huggingface_hub's [environment variables](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables): `HF_HOME` "Defaults to "~/.cache/huggingface" unless XDG_CACHE_HOME is set."
- [Ollama's OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility): "Ollama supports a subset of the OpenAI API", with streaming, tools and `response_format` among the parts it serves. Its release v0.40.6 serves `ollama-windows-amd64.zip` at 1,471,164,488 bytes and `ollama-darwin.tgz` at 174,459,907. Its model names, in `types/model/name.go`, carry no digest: "The digest check has been removed as is planned to be added back in at a later time."
- [llamafile's README at 0.10.6](https://github.com/mozilla-ai/llamafile/blob/0.10.6/README.md): "Only executables under 4GB can run on Windows". Its `docs/support.md`: "Windows 10+ (AMD64 only)". Its `llama.cpp` submodule is at llama.cpp's b10441.
- [Llama](https://llama.app): "Llama is an app for Mac and Windows that runs the latest open models on your computer", with a command-line version for Linux; "Point any app that works with OpenAI at localhost:9931/v1". Its install scripts fetch the build a `latest` pointer names, and check no checksum or signature.

## Why

llama-server is the only option that serves the whole API the labs teach from a small download on all six systems, pinned to the byte like a lab's other files. Ollama serves it too, but its install outweighs the model on Windows and Linux, and its models move with their tags. llamafile leaves out Windows on ARM. Serving the model from Python would mean writing the server the labs are about. Reasoning stays off because the model card makes it the default and warns of thinking loops, and because the learner's own token counts then match the server's. The strongest case against: on a Windows 11 machine whose Smart App Control enforces, the unsigned server can't run at all, and a machine without the Visual C++ runtime needs it installed. The labs still run there, since their tests never call the real model, but the learner can't try their code against it.

## Consequences

The first `model` command fetches about 850 MB, and later ones start at once, in any lab. A learner frees the space by deleting `sulba` from their cache folder. llama.cpp releases a build every few hours, so the pinned build moves by hand, after the spike's checks, when a lab needs a newer one. No number a lab shows comes from the real model, since its words differ between machines (record 31). A lab's page credits its model and says how much the command fetches and from where, as it does for fetched files, and the Privacy Policy says that the runner fetches from GitHub and Hugging Face when asked.

## Revisit when

llama.cpp signs its Windows builds or ships their runtime with them, a lab needs a model that llama-server can't run, or a lab's model is too slow without a GPU build.

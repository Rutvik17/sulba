# 17. Run every lab and model on the learner's device

- Status: accepted
- Date: 2026-10-14
- Supersedes: [5. Run learners' code in the browser and on their machine](0005-run-learner-code-in-the-browser-and-on-their-machine.md)

## Context

Record 5 runs learners' code in the browser through Pyodide, and everything else on their machine through the `sulba` command. It also sends learners without a capable machine to free cloud workspaces, and plans server sandboxes once certificates need results Sulba can trust. The course plan adds hosted models for subscribers, a tutor on paid inference providers and rented GPUs for Elite's newest-GPU labs. Sulba's bill has to stay at $0, with no cloud GPU and no hosted inference. The AI Engineering course needs Python and classical machine learning, then PyTorch, open language models, fine-tuning, C++ and CUDA.

## Decision

- **Where code runs:** every lab, and every model a lab uses, runs on the learner's own device. Code that needs only the libraries Pyodide ships runs in the browser, in a Web Worker. Everything else runs on the learner's machine through the `sulba` command: locked Python environments for PyTorch and training, a local model server for language models, and Docker images where a compiled toolchain needs one.
- **Models:** learners download open models from the Hugging Face Hub, pinned to a commit. A learner may also point a lab at a provider's API with their own key, which stays on their device and is never needed to pass.
- **What Sulba runs:** no learner code and no model. There are no hosted models, server sandboxes, GPU queue or cloud fallbacks, so results stay practice and there are no certificates.
- **Machines:** each level states the machine it needs before it begins. Beginner and Intermediate run on any laptop; from Advanced on, a level needs an NVIDIA GPU.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| The learner's browser and machine only (chosen) | Costs Sulba nothing; the learner's code and data stay with them; a browser run answers in about a second | Results can't back a certificate; a learner with only a Mac stops after Intermediate; setup on the learner's machine can fail |
| Free cloud workspaces as a fallback: Codespaces, Colab, Kaggle | Learners without a capable machine can take the GPU levels | Not on the learner's device; Codespaces has CPUs only and Colab's free GPUs aren't guaranteed; a second environment to support |
| Server sandboxes for trusted grading | Results Sulba can trust, the basis for certificates | About $0.0005 per graded run, paid by Sulba |
| A GPU queue | CUDA labs for learners without an NVIDIA GPU | $0.10 to $0.66 per learner per CUDA lesson, paid by Sulba |
| Hosted models for subscribers | Language-model labs on large models, with nothing to install | A bill that grows with every learner and every token |

## Evidence

- Pyodide's packages, uv's PyTorch indexes, Docker's GPU support, the free workspaces' limits and the sandbox and GPU estimates are in [record 5](0005-run-learner-code-in-the-browser-and-on-their-machine.md); they still hold.
- The Hugging Face Hub limits anonymous downloads per IP address, at 3,000 file requests per five minutes, so a learner's downloads never reach Sulba's bill ([Hub rate limits](https://huggingface.co/docs/hub/rate-limits)).
- llama.cpp's `llama-server` is MIT-licensed, serves an OpenAI-compatible API and downloads models from the Hub itself ([server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)).
- WebGPU, which in-browser models need, is fully supported in 85.8% of browsers in use and partly in 3.7% more ([caniuse](https://caniuse.com/webgpu)).
- QLoRA fine-tuning needs at least 3.5 GB of GPU memory for a 3B model and 6 GB for an 8B one ([Unsloth requirements](https://docs.unsloth.ai/get-started/beginner-start-here/unsloth-requirements)), within an 8 GB NVIDIA card.
- 32.9% of developers use macOS at work ([Stack Overflow 2025](https://survey.stackoverflow.co/2025/technology#most-popular-technologies-op-sys)), and CUDA needs an NVIDIA GPU.

## Why

Every alternative either adds a bill that grows with learners or sends them to a cloud environment that isn't theirs. The browser covers Python and classical machine learning, and the learner's machine covers PyTorch, language models and fine-tuning, with small open models where the lesson allows. The strongest case against: without results Sulba can trust there are no certificates, and a learner with only a Mac can't take the GPU levels.

## Consequences

Results are practice, as browser runs already are, and a learner's portfolio is their own lab code. Intermediate is where the course plan says applied-AI and forward-deployed learners are ready to interview, so the levels that need an NVIDIA GPU serve the roles whose learners tend to own one. Labs that use a language model can't be graded on its live output, which varies between runs and machines; how they're graded gets its own record with the first such lab, as do the `sulba` command's distribution, the local model server and model pinning. Setup on the learner's machine becomes the riskiest part of the product, so the command is tested on clean Windows, macOS and Linux machines before the first lab that needs it.

## Revisit when

Paying learners can cover server costs and want certificates, or PyTorch gains a usable build for the browser.

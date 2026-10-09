# 5. Run learners' code in the browser and on their machine

- Status: accepted
- Date: 2026-10-09

## Context

Every session is graded by real tests. Running learners' code on Sulba's servers costs money per run and needs hardened sandboxes, and Sulba stays at $0 until paying learners cover its costs. The AI Engineering course needs Python, NumPy and classical machine learning first, then PyTorch, C++ and CUDA.

## Decision

Code that needs only the libraries Pyodide ships runs in the browser, through Pyodide in a Web Worker. Everything else runs on the learner's machine through the `sulba` command, which sets up what each module needs: a locked Python environment for PyTorch and its libraries, and Docker images where a compiled toolchain needs one. Learners without a capable machine use a free cloud workspace, where the same command runs the same tests. Server sandboxes come only when certificates need results Sulba can trust.

## Options

| Where code runs | Cost to Sulba | What runs there | Can a result be trusted? |
| --- | --- | --- | --- |
| The browser (Pyodide 314) | $0 | Python 3.14.2 with pytest 9.0.2, NumPy 2.4.6, SciPy 1.18.0, pandas 3.0.2, scikit-learn 1.8.0, XGBoost 2.1.4, LightGBM 4.6.0 and Matplotlib 3.10.8. Not PyTorch, JAX or TensorFlow | Practice only, since the learner controls the browser |
| The learner's machine | $0 | Everything. PyTorch uses an NVIDIA GPU through CUDA, an Apple GPU through MPS, or the CPU | Practice only |
| A free cloud workspace | $0 | GitHub Codespaces: everything on a CPU, about 60 hours a month. Colab and Kaggle notebooks: PyTorch on a GPU, when one is free | Practice only |
| A server sandbox (a microVM) | About $0.0005 per graded run | Everything except GPU work | Yes: the basis for certificates |
| A GPU queue | $0.10 to $0.66 per learner per CUDA lesson | CUDA | Yes |

## Evidence

- Pyodide's packages and versions are from [`pyodide-lock.json`](https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide-lock.json) in Pyodide 314.0.7, which has no build of PyTorch, JAX or TensorFlow.
- uv installs the PyTorch build for the machine's accelerator from PyTorch's own package indexes ([uv's PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/)). PyTorch's `mps` device runs on Apple GPUs from macOS 14 ([PyTorch MPS](https://docs.pytorch.org/docs/2.14/notes/mps.html)).
- Docker Desktop passes a GPU to containers only on Windows with the WSL 2 backend ([Docker GPU support](https://docs.docker.com/desktop/features/gpu/)), so a Mac's GPU is out of reach inside a container. Python work therefore runs outside Docker.
- GitHub Codespaces includes 120 hours a month for personal accounts, counted at twice the clock time on the smallest (2-core) machine, so about 60 hours of use. It offers CPU machines only, and blocks rather than bills when the quota runs out without a payment method ([Codespaces billing](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces)). Colab's free GPUs are "not guaranteed and not unlimited", for sessions of at most 12 hours ([Colab FAQ](https://research.google.com/colaboratory/faq.html)).
- freeCodeCamp moved its Python curriculum into the browser so learners face "no waiting for a server" ([freeCodeCamp](https://www.freecodecamp.org/news/python-curriculum-upgrade)).
- Exercism runs every language's tests through one runner contract that writes `results.json` ([Exercism's test runner interface](https://github.com/exercism/docs/blob/main/building/tooling/test-runners/interface.md)). Sulba's run protocol follows the same pattern.
- The sandbox and GPU costs are estimates from e2b's and Modal's pricing.

## Why

A test run in the browser answers in about a second and costs nothing, and Pyodide covers Python, NumPy and classical machine learning. Deep learning needs PyTorch, which has no browser build, so it runs where it is fast and complete: on the learner's machine, with their GPU when they have one.

## Consequences

Pyodide is about 12 MB on the first visit, so it loads after the page is usable and is cached after that. Browser results can't back a certificate. Deep learning sessions need the `sulba` command, and CUDA sessions need an NVIDIA GPU, local or in a cloud notebook whose free GPUs aren't guaranteed. The course says so before those sessions begin.

## Revisit when

Learners want certificates, can't get a GPU for the CUDA work, or PyTorch gains a usable build for the browser.

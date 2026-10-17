# 27. Check a from-scratch build against a library's recorded results

- Status: accepted
- Date: 2026-10-17

## Context

Intermediate Module 1 builds neural networks from scratch in NumPy: an autograd engine, layers, losses and optimisers. Every from-scratch build is tested against a reference implementation, such as PyTorch, within a stated tolerance. A lab that needs only what Pyodide ships runs in the browser (record 17). Its tests run there in Pyodide, and in the content check in Pyodide and in CPython at the versions Pyodide ships, with the same results in each. Pyodide 314.0.7 ships NumPy, but neither PyTorch nor JAX. PyTorch's CPU wheel for Python 3.14 on Linux is 196 MB.

## Decision

- **Recordings:** a lab that builds what a library does has a `references/` folder: `make.py`, a script uv runs, and the JSON files it writes. `make.py` pins Python and each library it records with to an exact version in its inline script metadata, works out each case in float64, and writes the case's inputs beside the library's results, so nothing is made again from a seed. `lab.yaml` lists each file under `references`.
- **Tests:** every run of the lab has each file at `references/<file>`, beside the lab's data. A test reads it and compares the learner's results with the library's, within a tolerance the test states.
- **The check:** `pnpm check:references`, which CI's References job runs and deploys wait for, runs every `make.py` again into an empty folder. Every file it makes must be listed, and every listed file made again as the same JSON: the same keys, lengths and strings, and each number within 1e-12 of the recorded one, or for numbers above 1, within 1e-12 times the larger.
- **Serving:** the site serves each file as it serves datasets, at `/references/<hash>/<file>`, cached for good, and the workspace fetches them as the lab opens. A lab's download leaves them out, as it leaves out the tests.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Results recorded by a pinned script, recorded again in CI (chosen) | The library's own results, in every runner, the browser included; CI shows they still hold | Only the recorded cases are checked; a learner's own inputs can't be compared with the library |
| PyTorch in the content check's CPython only | Any input, checked live | The browser has no PyTorch, so the tests the learner runs couldn't be the ones the content check runs |
| A reference the course writes in NumPy | Runs in every runner | A second from-scratch build rather than a library's, and NumPy has no autograd |
| Expected values typed into the tests | Nothing to build | No code that runs in CI makes them |
| Finite differences (gradient checking) | Checks gradients on any input, with no library | Checks gradients against the learner's own forward pass, which can be wrong too |
| PyTorch on the learner's machine, through the lab's download (record 25) | The library itself, on any input | Every stage would need the download and a 196 MB install before its first test |

## Evidence

- Pyodide 314.0.7's lock file (`packages/lab/pyodide/pyodide-lock.json`) lists 359 packages for Python 3.14.2, NumPy 2.4.6 among them, and neither PyTorch nor JAX.
- PyTorch's [Reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html) note, for 2.14: "Completely reproducible results are not guaranteed across PyTorch releases, individual commits, or different platforms. Furthermore, results may not be reproducible between CPU and GPU executions, even when using identical seeds."
- [NEP 19](https://numpy.org/neps/nep-0019-rng-policy.html), NumPy's random number generator policy, status Final: "breaking stream-compatibility in order to introduce new features or improve performance will be allowed with caution", and "The standard practice now for bit-for-bit reproducible research is to pin all of the versions of code of your software stack, possibly down to the OS itself."
- uv's [Running scripts](https://docs.astral.sh/uv/guides/scripts/): "The inline metadata format allows the dependencies for a script to be declared in the script itself", and for the Python version a script requires, "uv run will search for and use the required Python version. The Python version will download if it is not installed".
- uv's [Using uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/): "Many PyTorch wheels are hosted on a dedicated index, rather than the Python Package Index (PyPI)"; "the +cpu builds are published on https://download.pytorch.org/whl/cpu"; and "We recommend the use of explicit = true to ensure that the index is only used for torch, torchvision, and other PyTorch-related packages, as opposed to generic dependencies like jinja2, which should continue to be sourced from the default index (PyPI)."
- PyPI has PyTorch 2.14.1 from 30 September 2026. PyTorch's CPU index serves `torch-2.14.1+cpu-cp314-cp314-manylinux_2_28_x86_64.whl` at 196,260,555 bytes.
- Locally, with PyTorch 2.14.1+cpu and NumPy 2.4.6, for a two-layer network on 256 rows of 128 features: `torch.get_default_dtype()` is `torch.float32`; the loss and gradients in float32 differ from those in float64 by up to 1.5e-8, measured as the check measures; in float64, one thread and four agree exactly; a NumPy build in float64 differs from PyTorch's by up to 1.1e-16; and three runs print the same bytes.

## Why

Recording brings the library's own numbers to the browser, where the learner runs the tests, and keeps every runner's results the same. Pinning the versions is what NumPy's policy asks of anyone who needs the same numbers again, and holding the inputs in the recording leaves nothing to a seed. Recording again in CI shows the files still hold what the library gives. Its margin leaves room for the last digits, which PyTorch doesn't promise across machines and which in float64 are about 1e-16 of a number, but not for a change in the numbers. The strongest case against: a test can only check the cases the author recorded, never the learner's own inputs.

## Consequences

A lab with references has its expected numbers in files that CI makes again; changing a case means running `make.py` and committing what it writes. The References job downloads each library once into uv's cache, which CI keeps while the `make.py` files stay the same. The packages a library pulls in aren't pinned, since they don't compute what's recorded. The margin suits float64, whose last digit is about 1e-16 of a number; in float32 it is about 1e-7, so a stage that teaches float32 still records in float64, and its tests compare at a tolerance they state.

## Revisit when

Pyodide ships PyTorch or another library a lab builds, or a stage needs to check inputs the learner chooses.

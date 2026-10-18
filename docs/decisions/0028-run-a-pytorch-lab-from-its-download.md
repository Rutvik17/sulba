# 28. Run a lab that needs PyTorch from its download, and bring its results back by a link

- Status: accepted
- Date: 2026-10-18

## Context

Intermediate's second module teaches PyTorch, so its labs' tests need torch. Pyodide doesn't ship it, and PyTorch publishes no WebAssembly build, so these labs run on the learner's machine (record 17). Record 25 downloads a lab as a project the learner runs with uv, but without its tests or checks, and nothing done there comes back to the site, so a stage passed there can't open the next one or count as progress. uv installs PyTorch's CPU builds from PyTorch's own index. The learner's code stays on their device, Sulba runs no server for it, and progress is a log of attempts (record 18).

## Decision

- **Machine labs:** a lab whose stages need a package Pyodide doesn't ship sets `runs: machine` in its `lab.yaml`, and all its stages run on the learner's machine. Its project pins torch from PyTorch's CPU index on every platform, and Python, pytest and each package its stages load that Pyodide ships at Pyodide's versions, so the code a learner wrote in the browser runs the same there. Torch's own dependencies are left to its resolver, since nothing of the lab runs in the browser.
- **The download:** a machine lab's download is record 25's project with a runner added: `sulba.py`; the pytest plugin and fixtures the browser runs; and `.sulba/lab.json`, which holds each stage's starter, tests and checks, and a Catch stage's fixed code. The learner's files start at the first stage they haven't passed, as the workspace would open it.
- **Running:** `uv run sulba.py` runs the current stage's tests and checks against the learner's files, and prints a result for each, with a Ship stage's notes. `uv run sulba.py finish` ends a Catch review. When a stage passes, it prints a link to the lab's page and opens it, and `uv run sulba.py next` starts the next stage.
- **The link:** its fragment holds the stages done there, with each Catch review, and their attempts as the attempts table takes them, each with an id made on the learner's machine, so a link opened twice adds nothing. It holds them as JSON compressed with DEFLATE, in base64url, and stays within 2,000 characters: when a stage took more runs than fit, the oldest stay out. The lab's page records them as the workspace records its own: the pass in this browser and, signed in, each attempt in the account. The page removes the fragment once it has read it.
- **Checks:** the content check runs a machine lab's stages and figures in CPython, in the lab's project. CI also runs each machine lab's download on Windows, macOS and Linux: there each stage's solution passes, its starter fails and its figures come out the same on all three.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| The download's own runner, with results brought back by a link (chosen) | Needs only uv, which record 25 already asks for; works in every browser, and on a machine the learner reaches over SSH, since the link is text; nothing on the learner's machine takes requests | The learner works in their own editor, not the site's, and opens a link after each stage |
| The workspace sends runs to a server on the learner's machine | The same workspace, editor and charts for every lab | Safari blocks it as mixed content; Chrome and Firefox first ask the learner to allow it; a server that runs code it is sent, kept from other sites only by checking where requests come from |
| The runner sends results to the learner's account | Nothing to open | Only for learners who sign in, and the runner needs a sign-in and a token of its own |
| The learner copies a result code into the page | Works everywhere | A step by hand after every stage, with nothing to click |
| The `sulba` command, published on PyPI | One tool for every lab that runs on the machine | A package to publish and keep in step with every lab, where uv already installs PyTorch |

## Evidence

- Pyodide 314.0.7's lock file lists 359 packages, none of them torch. PyTorch's CPU index lists torch 2.14.1 for CPython 3.14 on Linux (x86-64 and Arm), Windows on x86-64 and macOS 14 or later on Apple silicon, and no WebAssembly build. Its wheels are 196 MB for Linux on x86-64, 126 MB for Windows and 127 MB for macOS, and the Linux build takes 716 MB once installed.
- uv's [PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/): from PyPI, PyTorch installs "CPU-only wheels for Windows and macOS, and GPU-accelerated wheels on Linux"; its complete example "would use PyTorch's CPU-only builds on all platforms", from an index marked `explicit = true` "to ensure that the index is only used for torch, torchvision, and other PyTorch-related packages".
- PyTorch 2.14's [Reproducibility](https://docs.pytorch.org/docs/2.14/notes/randomness.html) note: "Completely reproducible results are not guaranteed across PyTorch releases, individual commits, or different platforms."
- Chrome's [Local Network Access](https://developer.chrome.com/blog/local-network-access) post: a request "from the public network to a local network or loopback destination" needs the user's permission, from Chrome 142. Firefox's [LocalNetworkAccess policy](https://mozilla.github.io/enterprise-admin-reference/reference/policies/localnetworkaccess/): its protections "require permission before a website can make requests to local or loopback addresses".
- WebKit's [bug 171934](https://bugs.webkit.org/show_bug.cgi?id=171934), still open, asks Safari to stop treating loopback addresses as mixed content. A comment of 25 March 2026, from a company whose web app talks to its own app on 127.0.0.1: "To be able to handle the connected appliances, we have to ask them to use Chrome." The latest, of 19 August 2026: "All vendors except Safari now ship LNA in stable."
- MDN's [URI fragment](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Fragment) page: "The fragment is not sent to the server when the URI is requested; it is processed by the client (e.g., the browser) after the resource is retrieved."
- Microsoft's [URL Length Limits](https://learn.microsoft.com/en-us/archive/blogs/ieinternals/url-length-limits): "WinINET.h defines INTERNET_MAX_URL_LENGTH as 2083 characters, and this limit remains in force in a number of places", and "there are code paths that will not handle URLs that exceed the legacy limit".
- Python's [webbrowser](https://docs.python.org/3/library/webbrowser.html): `open_new_tab` "Returns True if a browser was successfully launched, False otherwise", so the runner always prints the link as well.

## Why

The download already carries a pinned environment, and with its tests and a runner it carries the whole lab, so uv is all the learner installs. A link is text, so it reaches the site from any browser and from any machine the learner works on. Nothing listens on the learner's machine, so no website can reach their code through it. The strongest case against: a server on the learner's machine would keep the site's workspace, with its editor and charts, for every lab, but it would shut out Safari and ask every other browser's permission.

## Consequences

A machine lab's page has no editor. It shows each stage's brief, hints, explanation and solution, the download and the command, and the stages done; charts and Problem stages stay with labs that run in the browser. The learner needs uv and about 1 GB of disk, on Windows or Linux on x86-64, Linux on Arm, or macOS 14 or later on Apple silicon, which the level states before it begins: PyTorch 2.14 has no build for Intel Macs, or for Windows on Arm at Pyodide's Python. Results are practice, as in the browser, since the checks travel in the download as they do in the page. A machine lab's figures come from CPython alone, and each change to one runs its download on three systems in CI. The learner's files on their machine and the site's record of their passes are kept apart: downloading again starts from the course's solutions for the stages they've passed.

## Revisit when

Safari lets a page reach a server on the learner's machine, so the site's workspace could run a lab's tests there, or PyTorch runs in the browser.

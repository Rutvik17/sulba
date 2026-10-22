# Writing a course

A course is a folder of plain files (decision record 7). `pnpm check:content` checks every course on every pull request: each file against its schema, every stage in Pyodide and in CPython, every stage's prose with the numbers its `figures.py` gives, every chart as its `chart.py` draws it, and each lab project's lock.

## Layout

```text
<course>/
  course.yaml               id, title, and its levels, each with the machine it needs and its
                            modules in order
  modules/<module>/
    module.yaml             id, title, and its labs in order
    labs/<lab>/
      lab.yaml              id, title, summary, datasets, fetched files and ported code with
                            their credit, the files it gives, where its stages run, and its
                            stages in order
      data/<file>           each dataset lab.yaml lists: a .csv file, or a .json file for
                            records that nest
      references/           optional: the results of a library the lab's tests compare with:
                            each JSON file lab.yaml lists, and the make.py that records them
      given/<file>.py       optional, in a machine lab: code the lab gives its learner to
                            build on, each file lab.yaml lists in `given`
      project/              optional: what a download of the lab puts beside the learner's
                            files: README.md, pyproject.toml, uv.lock and a conftest.py if
                            it needs one
      stages/<stage>/
        stage.yaml          id, kind, title, what it builds on, the file the learner works in,
                            packages, minutes, a Catch stage's problems or a Ship stage's
                            checks, and a chart
        brief.md            the task
        hints.md            optional: hints in the order they open, separated by lines of ---
        explanation.md      the explanation
        starter/<file>      the code the stage starts from
        solution/<file>     the learner's file as it should be once the stage is done
        tests/test_*.py     pytest tests, each with @pytest.mark.id and a docstring as its name
        checks/test_*.py    a Catch or Ship stage's checks, written like tests
        figures.py          optional: computes the numbers the stage's prose shows
        chart.py            optional: draws the stage's chart with the learner's code
        cards.yaml          optional: the stage's review cards
```

A folder's name is its address in the URL. Order comes from the YAML files, which must list every folder there is and nothing else. A file the course doesn't use is an error. Hidden files and folders, whose names start with a dot, are left out.

## Ids

Every course, level, module, lab, stage, test and review card has a permanent id: a prefix (`crs`, `lvl`, `mod`, `lab`, `stg`, `tst`, `crd`), an underscore and six lowercase letters or digits, such as `stg_8k2m4q`. Progress and reviews are stored against ids, so an id is never changed or reused, even when its folder is renamed or moved.

## Stages

A lab's stages build on each other. A stage's tests run with the lab's data and the earlier stages' solutions. A lab that runs on the learner's machine can give code its learner builds on but doesn't write (decision record 37): each file `given` in `lab.yaml` lists, from `given/`, sits beside the learner's files in every run and in the download, and no stage's file may take its name. When an earlier stage made the same file, the stage's starter goes below the learner's code. `builds` in `stage.yaml` says what the stage builds on, in a line of Markdoc above its brief.

A stage's `kind` is `build`, `catch`, `ship` or `problem`. In a Build stage the learner writes the code. The checks hold each Build stage to three things:

- The solution passes every one of the stage's tests, and every earlier stage's.
- The starter fails at least one test.
- Every test has an id no other test has.

## Catch stages

In a Catch stage an assistant's code passes its own tests, and the learner reviews it before it's used. The starter is the assistant's code, in a file no earlier stage made, and `tests/` holds the assistant's own tests. `checks/` holds the hidden checks: each one tests the code the way it will really be used, and each finds one problem. `stage.yaml` lists the problems in the order the review shows them:

```yaml
problems:
  - check: tst_k3m8q2        # the id of the check that finds it
    title: It scored the wrong class
    cost: >-                 # what it would cost, in Markdoc
      ...
    fix: >-                  # how to fix it, in Markdoc
      ...
    edit:                    # the smallest change to the starter that fixes it alone
      replace: "predict_proba(X_new)[:, 0]"
      with: "predict_proba(X_new)[:, 1]"
```

The checks hold each Catch stage to these, besides the solution passing every test, check and earlier stage's test:

- The assistant's tests pass on its code, and every check fails on it.
- Each problem's edit appears once in the starter. Made alone, it passes the assistant's tests and that problem's check, and no other check.
- Each check belongs to exactly one problem.

A run shows the assistant's tests by name and only how many checks pass. When the learner finishes the review, the checks their code passes become their score, and each problem opens with what it costs and its fix, beside the explanation and the solution. The problems follow the explanation, or sit inside it where a line of `---` in `explanation.md` divides it. The page carries the checks, so a learner who reads its source can find them: runs in the browser are practice (decision record 17). A later stage on the same file builds on the learner's code if they caught every problem, and on the solution if they didn't.

### Drafting problems

A code model on your machine drafts a Catch stage's problems, and you choose among them. First write the stage's solution, the assistant's tests and the checks, with the solution as the starter for now and `problems: []` in `stage.yaml`. Then serve a code model with llama.cpp's `llama-server`, such as Qwen3-Coder:

```sh
llama-server -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M
```

On a GPU without room for the whole model, `--n-cpu-moe` keeps some of its layers on the CPU. Then draft:

```sh
pnpm --filter @sulba/content draft courses/<course>/modules/<module>/labs/<lab>/stages/<stage>
```

The model is shown the solution with its lines numbered, the assistant's tests, the name of each check, and the kinds of bug in `packages/content/src/faults.ts`. For each bug it names a line and writes what the assistant put there instead. A draft is kept only when the assistant's tests pass with it and exactly one check fails, and each run stops after a minute. The drafts kept go to the stage's `.drafts.yaml`, under the check each fails, with the edit that fixes it. `--server` gives another address than `http://127.0.0.1:8080`, `--rounds` how many times to ask (3), and `--count` how many drafts each time (8).

Choose one draft for each check: put its bug in the starter, and its edit in `problems` with a title, its cost and its fix. A kept draft fails the right check, but whether an assistant would write it, and whether it's worth a learner's time, is for you to judge. `.drafts.yaml` is never committed.

## Ship stages

In a Ship stage the learner's code must pass hidden tests, then the checks it needs before it ships. `tests/` holds the tests: a run shows each one by name and whether it passed, never what it was given, expected or printed. `checks/` holds the checks, and `stage.yaml` lists them in the order they show, each part a line of Markdoc:

```yaml
checks:
  - check: tst_k3m8q2        # the id of the check in checks/
    title: "Fast on {% $fig.samples %} samples"
    requires: >-             # what the check requires of the code
      `best_threshold` handles {% $fig.samples %} samples in under a second.
    failure: >-              # what the learner reads when the code fails it
      The limit is a second.
```

A check reports what it measured, such as the time the code took, with pytest's `record_property("note", ...)`, and a run shows it beside the check whether it passed or failed. A run in the browser stops at its time limit (`timeLimitMs` in `packages/lab/src/protocol.ts`), so a check that times the code keeps its own work well inside it.

A test of asyncio code asks for the `loop` fixture, an event loop whose clock jumps to its next timer instead of waiting (decision record 21). It runs a coroutine with `loop.run_until_complete(...)`, and `loop.time()` is the seconds that passed, the same in Pyodide and CPython, so a minute's timeout takes no time. Code that waits forever fails at once, and the code under test can't wait on sockets or threads.

A test of typed code asks for the `typecheck` fixture, with `mypy` among the stage's `packages`. `typecheck("shapes.py")` gives mypy's errors in the file under `--strict`, one line each as mypy prints them, such as `shapes.py:4: error: Function is missing a type annotation  [no-untyped-def]`, the same in Pyodide and CPython (decision record 22). mypy's first check takes seconds in a browser, so the browser makes it before a run's time starts.

A test of a FastAPI app, with `fastapi` and `httpx` among the stage's `packages`, sends its requests in process, as FastAPI's own async tests do: an `httpx.AsyncClient` over `ASGITransport(app=app)`, run with the `loop` fixture (decision record 24). There, a `def` endpoint or dependency runs on the loop instead of in anyio's worker threads, so it gives the same result in Pyodide, which has no threads, and in CPython. FastAPI's first import takes seconds in a browser, so the browser makes it before a run's time starts.

A test of code that calls a model asks for the `model` fixture, with `httpx`, or `openai`, among the stage's `packages`: a scripted model server that answers each chat request with the next reply the test gives it, in the form llama.cpp's llama-server gives it (decision record 31). `model.says("We open", " at 9.")` scripts a reply, in the pieces a stream sends it in, with `tool_calls`, `finish_reason`, `usage` and `after`, its wait in seconds, if the test needs them, and `probabilities`, for each piece the tokens the model weighed for its place and their probabilities, such as `[{"No": 0.9, "Yes": 0.1}]`, which a request that asks for logprobs gets. It answers a completion request, a prompt to go on from, with the next reply too. `model.fails(429, "Too many requests.", retry_after=2)` scripts an error, `model.hangs()` a request never answered, `model.disconnects()` a dropped connection, and `model.answers(function)` has a function script each reply the test didn't. It embeds and reranks too, as an embedding or reranking model does: `model.embeds({"When do you open?": [0.6, 0.8]})` gives each text the vector a mapping or a function of the text gives it, with `tokens`, a function that counts a text's tokens for the reply's `usage`, if the test needs it, and `model.ranks(function)` scores each document for a query, from a function of the two or a mapping of their pairs. A failure the test scripts answers the next request, whatever it asks for. Code reaches it through `model.client()` or `model.async_client()`, httpx clients whose base URL is its API, and `model.requests` holds what the code sent. A wait passes on the `loop` fixture's clock, and a request the test scripted no reply, vector or score for fails the test.

A test of the learner's own tests runs them inside itself with pytest's `pytester`, on the learner's code as it is and again with each problem planted in it. That run loads the runner's fixtures with `-p sulba_fixtures`, so the learner's tests can ask for `loop`, `typecheck` and `model` too. Each run is a pytest session of its own, which takes time in a browser, so a run with a problem planted stops at its first failure, with `-x`.

The stage passes when every test and check passes. Its explanation opens after the first run, with the solution. `pnpm check:content` holds a Ship stage to what it holds a Build stage to, with its checks counted among its tests. The stage's Output tab shows only what the code prints as it loads, since what it prints in a test could show the test's data.

## Problem stages

A Problem stage is an interview problem, solved against the clock (decision record 23). Its brief stays hidden until the learner starts, and its `minutes` are the time it has. The learner writes a plan first: how the code works, what it costs in time and space, and the inputs that could break it. The editor opens once the plan is written, and the plan stays in its own tab. The clock runs from the start whether the page is open or not. The explanation and the solution open when the code passes or the minutes are up, and the stage keeps the time from the start to the run that passed.

The starter is in a file no earlier stage made, since the learner solves the problem from nothing. `pnpm check:content` holds a Problem stage to what it holds a Build stage to. A test with a large input holds the code to the cost the explanation gives: a run stops at its time limit, so a slower way fails it.

## Projects

A lab whose code runs on the learner's machine, such as a web service, has a project (decision record 25). Its workspace then offers a download: one zip of the project's files, the lab's data and the learner's files as the stage open in the editor has them, made in the browser. `README.md` tells the learner how to run it with uv. `pyproject.toml` lists what it needs, at the versions the browser runs, and `uv.lock`, which `uv lock` writes, pins them. `pnpm check:content` holds the lock to `uv lock --check`, to the Python version Pyodide runs, to the version Pyodide ships of each package they both have, and to every package the lab's stages load. No learner's file may share a name with a project file.

### Labs that run on the learner's machine

A lab whose stages load a package Pyodide doesn't ship, such as `torch`, or need more data or time than a run in the browser has, sets `runs: machine` in `lab.yaml`, and all its stages run on the learner's machine (decision record 28). Its page shows each stage's brief, hints, explanation and solution, with no editor, and its download is the project with the stages' tests and checks and their runner, `sulba.py`, which the learner runs with `uv run sulba.py`. When a stage passes, the runner prints a link back to the lab's page, which marks the stage done there. Its `README.md` says so.

Its project pins torch from PyTorch's CPU index on every platform, through `[tool.uv.sources]` and an index marked `explicit = true`, and Python, pytest and each package its stages load that Pyodide ships at Pyodide's versions; torch's own dependencies are left to uv. `pnpm check:content` runs its stages and figures in CPython alone, in that project, and `pnpm check:machine`, which CI's Machine labs jobs run on Windows, macOS and Linux, runs its download through `uv run sulba.py` with each stage's starter and solution, and CI fails when a stage's figures differ from one system to another. Such a lab has no Problem stages and no charts, which run in the browser, and no learner's file named `sulba.py`.

Each figure must come out the same on every system. Counts, sizes and exact roundings do, and so does a float64 run whose results stand clear of the last digits a system's sums can change, which `figures.py` asserts. No figure comes from float32 or bfloat16 training. Float64 training still drifts apart from one system to another, as kernels sum in different orders and each step grows the difference, so a figure read from a long run is stated as a bound that `figures.py` asserts.

On some Windows machines, the process ends at PyTorch's first bfloat16 matrix multiply, which oneDNN runs. A test or check that runs bfloat16 turns oneDNN off first, with `monkeypatch.setattr(torch.backends.mkldnn, "enabled", False)`, so PyTorch runs bfloat16 in its own kernels.

### Fetched files

A lab that runs on the learner's machine can fetch files too large for the site to serve, such as a dataset or a model's weights, from their publisher (decision record 29). `fetch` in `lab.yaml` lists each source with its credit, and each of its files with the address its publisher serves it from, its size in bytes and its sha256:

```yaml
fetch:
  - kind: data               # data, or model for a model's weights
    title: Fashion-MNIST
    creators: [Zalando Research]
    url: https://github.com/zalandoresearch/fashion-mnist
    licence:
      name: MIT
      url: https://github.com/zalandoresearch/fashion-mnist/blob/master/LICENSE
    files:
      - file: t10k-labels-idx1-ubyte.gz
        url: https://fashion-mnist.s3.eu-central-1.amazonaws.com/t10k-labels-idx1-ubyte.gz
        bytes: 5148
        sha256: 67da17c76eaffca5446c3361aaab5c3cd6d1c2608764d35dfb1850b086bf8dd5
```

Take the address from the publisher's own page, over HTTPS, and the size and sha256 from a copy fetched from it. Before a run, the runner fetches into the download's `data/` each file that is missing or doesn't match, and a run has it at `data/<file>`, beside the lab's datasets, which keep their own names. Runs only read a fetched file: `pnpm check:content` fails when one changes it. The checks and the build fetch each file too, and keep it under its sha256 in `node_modules/.cache/sulba-fetched`, which CI keeps between runs; each process checks its copy against the sha256 before using it. The lab's page credits each source and says how much the first run downloads and from where, so the project's `README.md` says so too. A file is used only under a licence that allows a paid course, as for a dataset.

### A lab's models

A lab that runs on the learner's machine can name models, which `uv run sulba.py model` serves there with one llama.cpp server, for the learner's code to call by each one's title at `http://127.0.0.1:9931/v1` (decision record 34): a chat model through the chat completions API, an embedding model through `/v1/embeddings` and a reranker through `/v1/rerank`. Each entry in `models` in `lab.yaml` gives the model's title, its kind, which is `chat`, `embedding` or `reranking`, its credit, and its GGUF file's address, size and sha256, and a chat model's entry can give a `context`:

```yaml
models:
  - title: Qwen3.5-0.8B
    kind: chat
    creators: [Qwen]
    url: https://huggingface.co/Qwen/Qwen3.5-0.8B
    licence:
      name: Apache License 2.0
      url: https://huggingface.co/Qwen/Qwen3.5-0.8B/blob/2fc06364715b967f1860aea9cf38778875588b17/LICENSE
    file:
      url: https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF/resolve/8fea620810c4afa23dd6443f999a48574c1611a3/Qwen3.5-0.8B-Q8_0.gguf
      bytes: 833592096
      sha256: 37ae482d336108d23516fa35e8e0c4126688d81018b87178a18d752a1357814f
```

A title has only letters, digits, dots, dashes and _, and each model in a lab has a title of its own. The first time a learner runs the command, the runner fetches the models and the build of llama.cpp's server for their system, which `sulba.py` pins, into `sulba` in their cache folder, where every lab finds them. It loads every model before it says they answer, and answers at the lab's address itself, passing each request on to the server, so that a program's connection stays open from one request to the next (decision record 35). A chat model reads a conversation of up to 4,096 tokens, or of up to its `context`, a multiple of 1,024 from 4,096 to 32,768, for a lab whose conversations are longer, such as an agent's with its tools' results (decision record 36), with reasoning off; an embedding model embeds a text of up to 2,048 tokens; and a reranker scores a query and a passage of up to 2,048 tokens together. Where a model was trained on fewer tokens, the server holds it to those. On macOS, a chat model runs on the GPU and the others on the CPU. A lab's tests never call the models: they call the `model` fixture's scripted model (decision record 31), so no figure comes from a real model. The lab's page credits each model and says how much the command downloads and from where, so the project's `README.md` says so too. `pnpm check:machine --model`, which CI's Models jobs run on Windows, macOS and Linux, asks each model one thing, as its kind allows, from the download of a lab that serves it.

### A lab's database

A lab that runs on the learner's machine can keep data in Postgres, with pgvector (decision record 33). Its project locks `embedded-postgres`, whose wheel brings Postgres 18 and pgvector for each system, and `psycopg` to reach it, and a stage that imports psycopg lists it under `packages`. On Linux, the runner uses the PostgreSQL project's own pgvector instead, which `sulba_fixtures.py` pins, fetched the first time into `sulba` in the learner's cache folder: the wheel's build there runs only on processors like the one that built it. A test asks for the `database` fixture and gets the address of a new, empty database with pgvector installed, as a `postgresql://` URL that psycopg connects to:

```python
def test_nearest(database):
    with psycopg.connect(database) as conn:
        ...
```

The run starts one server for its tests, on 127.0.0.1 at a free port, with a password it makes, and stops it and deletes its files when they're done. Postgres doesn't run as root, so neither does a run that asks for a database. On Windows, pgvector needs a processor with AVX2, and Postgres needs the lab's folder to have a name the system's code page can write. `uv run sulba.py db` starts the lab's database for the learner's own code, at `postgresql://postgres:<password>@127.0.0.1:5432/postgres`, until Ctrl+C, and keeps what's in it in the download's `.sulba/database`. A test never uses that database, so a run gives the same result whatever the learner has put there.

### A lab's Spark

A lab that runs on the learner's machine can run Spark's DataFrame API and Spark SQL on Sail, an engine that speaks Spark Connect, which the run starts in its own process (decision record 41). Its project locks `pysail` and `pyspark-client` at the versions Sail's documentation pairs, and pandas below 3, which PySpark's client doesn't yet fully support, and a stage that imports pyspark lists `pyspark-client` under `packages`. A test asks for the `spark` fixture and gets a Spark session:

```python
def test_totals(spark):
    orders = spark.createDataFrame(
        [("UK", 120.5), ("US", 15.25)], "country STRING, amount DOUBLE"
    )
    ...
```

The run starts one Sail server for its tests, on 127.0.0.1 at a free port, which they share. It splits work into two partitions, so a sum of floats comes out the same on every machine, and the session's time zone is UTC. When a test ends, its temporary views are dropped. Sail has no build for Windows on Arm.

`pnpm check:machine --spark`, which CI's Spark job runs on Linux, runs the lab's download on Spark itself, with PySpark in place of `pysail` and `pyspark-client`, and each stage's solution must pass there too. Sail and Spark differ in places, so a stage keeps to what both do alike: a CSV it reads has as many fields in each row as in its header, its integer sums stay within their type, and its tests check an exception's class but not its message, compare floats with a tolerance, and compare timestamps formatted as strings in Spark, since a collected timestamp is a datetime in the machine's own time zone.

### TypeScript stages

A lab that runs on the learner's machine can have stages in TypeScript (decision record 39): the stage's file is a `.ts` file, its tests and checks are `<name>.test.ts` files, and the lab can give `.ts` files too. Its project then holds a `package.json`, which sets `"type": "module"` and names the packages the tests and the learner's code use, typescript and `@types/node` among them; the `package-lock.json` that `npm install --package-lock-only` writes from it; and a `tsconfig.json`, which includes the files tsc checks, with `"noEmit": true` and `"allowImportingTsExtensions": true`. Every run of the lab has the three beside the learner's files. Before a learner's first TypeScript run, the runner fetches Node.js, the build for their system that `sulba_runner.py` pins by its size and sha256, and installs the lock's packages with `npm ci --ignore-scripts`, each once, into `sulba` in their cache folder.

A run checks the session's files with the lab's tsc first: its first error is the run's problem, and the tests don't run. Then Node's test runner runs the tests. Node strips the types and runs the rest as JavaScript, so the files use only TypeScript that can be erased: no enums or parameter properties. A test's id starts its name:

```ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { statement } from '#statement.ts';

test('tst_demo27 Shows each entry with its sign', () => {
  assert.deepEqual(statement([12, -5]).slice(0, 2), ['+12', '-5']);
});
```

Tests import the learner's files, and the files the lab gives, through `"imports": { "#*": "./*" }` in `package.json`, as `#statement.ts`, so they find them from `tests/`, from `tests/checks/` and from where a later stage's runs put the earlier stages' tests. A failed `assert.equal` or `assert.deepEqual`, or one of their strict forms, shows the value the test expected and the one it got. A run with tests in both languages runs each with its own runner. The lab's page says that the first run downloads Node.js from nodejs.org and the lab's packages from registry.npmjs.org, so the project's `README.md` says so too.

A lab whose TypeScript makes a page for the browser also has a `tsconfig.build.json` in its project, which names the files to compile, with `"rootDir"` and `"outDir"`, and `"rewriteRelativeImportExtensions": true` so that an import of `./chat.ts` loads `./chat.js`. `uv run sulba.py build` compiles them with the lab's tsc, and `pnpm check:machine` builds the stages' solutions so.

## Review cards

Once a learner passes a stage, its cards come back for spaced review (decision record 20). `cards.yaml` lists them, each side in Markdoc with the stage's figures:

```yaml
cards:
  - id: crd_4n7q2x
    front: What does the sigmoid of a score give?
    back: The probability that the sample is in class 1.
```

A card asks one thing, and its answer is short enough to recall in full. Reviews are stored against a card's id, so a card that is reworded keeps its id and its schedule, and a card that asks something else takes a new id. Changing a card leaves its stage's version as it was.

## Prose, formulas and numbers

Prose is Markdoc, with no tags and no HTML.

Formulas are TeX, rendered to MathML when the site is built (decision record 15). A formula on its own lines is a fenced block marked `math`. A formula in a sentence is inline code wrapped in dollars:

````markdown
```math
\sigma(z) = \frac{1}{1 + e^{-z}}
```

The sigmoid `$\sigma(z)$` is a probability.
````

A displayed formula never breaks across lines by itself, and one wider than the text scrolls sideways, so a long one is split with `aligned`, aligned at the `=`, to fit a phone.

A table wider than the text scrolls sideways too. A table's header row is set in capitals, so a symbol in it is written as a formula: `` `$\lambda$` `` shows λ, where a plain λ would show Λ.

Numbers are never typed. `figures.py` defines `figures()`, which returns each number as a string, formatted as the prose shows it. It runs beside the lab's data. A formula shows one as `\fig{name}`, and a sentence as `{% $fig.name %}`. The checks fail on any of these:

- a formula that doesn't render;
- a tag inside code, which code shows as written, so a figure goes outside the code;
- a figure the prose names that `figures.py` doesn't give, or one it gives that the prose never shows;
- figures that differ between Pyodide and CPython;
- a character in a formula that the math font has no glyph for.

## Charts

A stage can have a chart that draws the learner's own code (decision record 16). Until the stage is passed, it shows the solution's drawing, faded, and its sliders stay where they start. `chart.py` defines `chart()`, which runs beside the lab's data and the learner's files, imports the functions it draws, and takes each slider's value by its name. It returns what to draw:

```python
{
    # Each axis: the values it spans, the step between its labelled ticks, its name.
    "x": {"min": -8, "max": 8, "step": 2, "label": "x"},
    "y": {"min": 0, "max": 1, "step": 0.25, "label": "probability"},
    # Drawn in order, so the last lies on top.
    "lines": [{"style": "main", "label": "Your sigmoid", "x": x, "y": yours}],
    "points": [{"x": 0, "y": 0.5}],
    "readouts": [{"label": "Probability at x = 0", "value": "0.5000"}],
    # What a screen reader reads in place of the chart.
    "description": "Your sigmoid with w = 1 and b = 0",
}
```

A line's style is `main`, the learner's own result; `base`, a curve to read it against; `faint`, a result to compare with; or `dashed`, a level such as a target. Its label names it in the legend, which lists the line drawn last first. NumPy arrays and numbers can go in as they are, and a number that isn't finite breaks its line. A readout is a value as the page shows it, under a short label. Labels name what a number is, not how it was worked out.

`stage.yaml` gives the chart's title and its sliders:

```yaml
chart:
  title: Sigmoid
  sliders:
    - name: w                # the argument chart() takes the value as
      label: Weight w
      min: 0.25
      max: 4
      step: 0.05
      value: 1               # where it starts
    - name: lr
      label: Learning rate
      stops: [0.05, 0.5, 5]  # values to move through, in place of a range
      value: 0.5
```

The checks draw each chart with the stage's solution at its sliders' first values, and at each end of each slider with the others at their first, in Pyodide and in CPython. They fail if `chart.py` raises an error or returns something the page can't draw, and if the runtimes draw differently at the first values. Elsewhere they may: training that never settles turns their last-digit differences into visible ones.

## Data

A lab's data file is built by a script in `tools/datasets` from the provider's own file, checked by its sha256, and `lab.yaml` credits it with what was changed. A dataset is used only under a licence that allows a paid course, such as CC BY 4.0, read on the provider's own page.

## References

A lab that builds what a library does, such as an autograd engine PyTorch already has, checks the learner's code against the library's own results (decision record 27). The library doesn't run in the browser, so its results are recorded: `references/make.py`, a script uv runs, pins the library and the versions it records with, works out each case in float64, as NumPy does by default and PyTorch only when asked, and writes the case's inputs and the library's results as JSON. `lab.yaml` lists each file under `references`, and every run has it at `references/<file>`, beside the lab's data, where a test reads it and compares the learner's results with it within a tolerance the test states.

`uv run make.py <folder> <data>` writes the files into `<folder>`, and finds in `<data>` the lab's data as a run has it in `data/`: its datasets and the files it fetches, each by its name (decision record 30). A make.py that reads no data ignores `<data>`, and writes into its own folder when given no folder. A recording holds its inputs too, rather than a seed to make them again, since NumPy's `Generator` doesn't promise the same random numbers from one version to the next. `pnpm check:references`, which CI's References job runs, records every lab's references again, and fails when a file is missing or not listed, or isn't the same JSON as before: the same keys, lengths and strings, and each number within 1e-12 of the recorded one, or for numbers above 1, within 1e-12 times the larger, since a library's results can differ in their last digits from one machine to another.

## Ported code

A lab can port code by others, such as a JavaScript library rewritten in Python. The code's licence must allow a paid course, as MIT does, and `lab.yaml` credits it under `code`. Its page links the code and its licence and carries the notice the licence asks every copy to keep:

```yaml
code:
  - title: superstruct 2.0.2
    creators: [Ian Storm Taylor]
    url: https://github.com/ianstormtaylor/superstruct/tree/v2.0.2
    licence:
      name: MIT
      url: https://github.com/ianstormtaylor/superstruct/blob/v2.0.2/License.md
    notice: >-                 # the copyright and permission notice, word for word
      ...
    changes: Ported to Python, with its tests.
```

## Code style

Course code follows the rules and style the editor applies to learners' code (`ruff.toml`), and `pnpm lint:python` checks it.

## Licence

Course content is all rights reserved ([LICENSE](LICENSE)). Each dataset, each fetched file, and the code by others a lab ports, keeps its own licence, credited in its lab's `lab.yaml`.

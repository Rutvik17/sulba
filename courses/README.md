# Writing a course

A course is a folder of plain files (decision record 7). `pnpm check:content` checks every course on every pull request: each file against its schema, every stage in Pyodide and in CPython, every stage's prose with the numbers its `figures.py` gives, and every chart as its `chart.py` draws it.

## Layout

```text
<course>/
  course.yaml               id, title, and its levels, each with its modules in order
  modules/<module>/
    module.yaml             id, title, and its labs in order
    labs/<lab>/
      lab.yaml              id, title, summary, datasets with their credit, and its stages in order
      data/<file>.csv       each dataset lab.yaml lists
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
```

A folder's name is its address in the URL. Order comes from the YAML files, which must list every folder there is and nothing else. A file the course doesn't use is an error. Hidden files and folders, whose names start with a dot, are left out.

## Ids

Every course, level, module, lab, stage and test has a permanent id: a prefix (`crs`, `lvl`, `mod`, `lab`, `stg`, `tst`), an underscore and six lowercase letters or digits, such as `stg_8k2m4q`. Progress is stored against ids, so an id is never changed or reused, even when its folder is renamed or moved.

## Stages

A lab's stages build on each other. A stage's tests run with the lab's data and the earlier stages' solutions. When an earlier stage made the same file, the stage's starter goes below the learner's code. `builds` in `stage.yaml` says what the stage builds on, in a line of Markdoc above its brief.

A stage's `kind` is `build`, `catch` or `ship`. In a Build stage the learner writes the code. The checks hold each Build stage to three things:

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

The stage passes when every test and check passes. Its explanation opens after the first run, with the solution. `pnpm check:content` holds a Ship stage to what it holds a Build stage to, with its checks counted among its tests. The stage's Output tab shows only what the code prints as it loads, since what it prints in a test could show the test's data.

## Prose, formulas and numbers

Prose is Markdoc, with no tags and no HTML.

Formulas are TeX, rendered to MathML when the site is built (decision record 15). A formula on its own lines is a fenced block marked `math`. A formula in a sentence is inline code wrapped in dollars:

````markdown
```math
\sigma(z) = \frac{1}{1 + e^{-z}}
```

The sigmoid `$\sigma(z)$` is a probability.
````

A displayed formula never breaks across lines by itself, so a long one is split with `aligned`, aligned at the `=`, to fit a phone.

Numbers are never typed. `figures.py` defines `figures()`, which returns each number as a string, formatted as the prose shows it. It runs beside the lab's data. A formula shows one as `\fig{name}`, and a sentence as `{% $fig.name %}`. The checks fail on any of these:

- a formula that doesn't render;
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

## Code style

Course code follows the rules and style the editor applies to learners' code (`ruff.toml`), and `pnpm lint:python` checks it.

## Licence

Course content is all rights reserved ([LICENSE](LICENSE)). Each dataset keeps its own licence, credited in its lab's `lab.yaml`.

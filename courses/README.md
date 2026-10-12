# Writing a course

A course is a folder of plain files (decision record 7). `pnpm check:content` checks every course on every pull request: each file against its schema, every stage in Pyodide and in CPython, and every stage's prose with the numbers its `figures.py` gives.

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
        stage.yaml          id, kind, title, the file the learner works in, packages, minutes,
                            and a Catch stage's problems
        brief.md            the task
        hints.md            hints in the order they open, separated by lines of ---
        explanation.md      the explanation
        starter/<file>      the code the stage starts from
        solution/<file>     the learner's file as it should be once the stage is done
        tests/test_*.py     pytest tests, each with @pytest.mark.id and a docstring as its name
        checks/test_*.py    a Catch stage's hidden checks, written like tests
        figures.py          optional: computes the numbers the stage's prose shows
```

A folder's name is its address in the URL. Order comes from the YAML files, which must list every folder there is and nothing else. A file the course doesn't use is an error. Hidden files and folders, whose names start with a dot, are left out.

## Ids

Every course, level, module, lab, stage and test has a permanent id: a prefix (`crs`, `lvl`, `mod`, `lab`, `stg`, `tst`), an underscore and six lowercase letters or digits, such as `stg_8k2m4q`. Progress is stored against ids, so an id is never changed or reused, even when its folder is renamed or moved.

## Stages

A lab's stages build on each other. A stage's tests run with the lab's data and the earlier stages' solutions. When an earlier stage made the same file, the stage's starter goes below the learner's code.

A stage's `kind` is `build` or `catch`. In a Build stage the learner writes the code. The checks hold each Build stage to three things:

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

A run shows the assistant's tests by name and only how many checks pass. When the learner finishes the review, the checks their code passes become their score, and each problem opens with what it costs and its fix, beside the explanation and the solution. The page carries the checks, so a learner who reads its source can find them: runs in the browser are practice (decision record 5). A later stage on the same file builds on the learner's code if they caught every problem, and on the solution if they didn't.

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

## Data

A lab's data file is built by a script in `tools/datasets` from the provider's own file, checked by its sha256, and `lab.yaml` credits it with what was changed. A dataset is used only under a licence that allows a paid course, such as CC BY 4.0, read on the provider's own page.

## Code style

Course code follows the rules and style the editor applies to learners' code (`ruff.toml`), and `pnpm lint:python` checks it.

## Licence

Course content is all rights reserved ([LICENSE](LICENSE)). Each dataset keeps its own licence, credited in its lab's `lab.yaml`.

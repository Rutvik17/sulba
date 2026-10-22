# 37. Give a machine lab code its learner builds on

- Status: accepted
- Date: 2026-10-22

## Context

A lab's stages build on each other: each stage works in one file, and a stage's run has the lab's data and the earlier stages' files as the learner left them. Code a lab gives without the learner writing it has had to go in a stage's starter, below or around the part the learner writes. Intermediate's Shipping full stack module puts the help desk's agent behind a web app. Each of its labs builds on what the one before built: the agent and its tools, then the API, then the database, then sign-in. The learner writes the lab's own part, and the rest comes with the lab. That rest is several files, about a thousand lines, which no stage of the lab makes. A starter that held it would bury the learner's file in code they don't write, and a later lab would carry the earlier labs' code in its own starters.

## Decision

- **The files:** a lab lists the Python files it gives in `given` in `lab.yaml`, each in its `given/` folder. A stage's file can't take a given file's name, nor can a given file take one of the lab's project files' names, or `sulba.py` or `figures.py`.
- **Runs:** every run of the lab's stages has each given file beside the learner's files, in the content check, the machine check and the learner's own runs. Figures run with them too.
- **The download:** the site serves each given file with the lab's project files, and a download puts it beside the learner's files. `lab.json` names them, so `sulba.py` puts them in each run.
- **Where:** only a lab that runs on the learner's machine gives files. A lab in the browser keeps its given code in a starter, since its page shows the learner every file a run of theirs has.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Files in the lab's `given/`, in every run and the download (chosen) | The learner's file holds only their own code; a lab can give as many files as an app has; the content check runs the given code with every stage | Given code is copied from lab to lab where a later lab builds on an earlier one's |
| Given code in a stage's starter | Nothing to build | Only one file a stage, around the learner's own code; a later lab's starters carry the earlier labs' code |
| A package the lab's project installs from PyPI | One copy of the code for every lab | A package to publish, version and keep, for code the course itself writes |
| One long lab for each module's app | Each stage's files carry on to the next | A module of 50 hours in one lab, against the course plan's labs of about 10 |

## Evidence

- `courses/README.md`: "A lab's stages build on each other. A stage's tests run with the lab's data and the earlier stages' solutions", and a lab project holds "README.md, pyproject.toml, uv.lock and a conftest.py if it needs one".
- Python's documentation on [the initialization of sys.path](https://docs.python.org/3/library/sys_path_init.html): "The first entry in the module search path is the directory that contains the input script, if there is one." So under `uv run sulba.py` the download's folder is importable, but a run's own folder holds only the files the runner writes there, and a test that opens a given file by its path finds it only when the runner writes it.
- The course plan's Intermediate table gives Shipping full stack 50 hours for "A TypeScript front end; a Python API; Postgres; sign-in; Docker; deploying to a public cloud; logs and monitoring", and one lab: "The agent behind a web app with sign-in and a dashboard of cost and latency".

## Why

The learner's file stays theirs, as in every other lab, while a module's app grows across labs of a usual size. The given code is checked as the learner's is: every stage runs with it, so code that no longer works with a stage fails the content check. The strongest case against: a later lab copies an earlier lab's code into its own `given/`, so a fix to that code is made in each lab that carries it.

## Consequences

A lab with given files is a machine lab. Its download carries the given files like its project files, and its page doesn't show them. A lab that gives code an earlier lab built copies the earlier lab's solution into its `given/`.

## Revisit when

A lab in the browser needs code it gives, or the same given file is copied into more than three labs.

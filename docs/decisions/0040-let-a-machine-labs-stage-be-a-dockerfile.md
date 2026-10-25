# 40. Let a machine lab's stage be a Dockerfile, read by its tests and built in CI

- Status: accepted
- Date: 2026-10-22

## Context

Shipping full stack's last lab ships the help desk: its logs, its health checks, and the image it runs from on a host. The learner writes that image's Dockerfile, so a stage's file must be able to be one. A stage's tests run wherever the lab runs, through `uv run sulba.py` on the learner's machine and in CI on Windows, macOS and Linux (decision record 28), with nothing to install but uv. Docker is not something every learner has: Docker Desktop is free for personal use and small companies only, and GitHub's macOS runners have no Docker at all. The content check has to know that a stage's Dockerfile does what its tests say, and that the solution's image builds.

## Decision

- **The file:** a stage of a lab that runs on the learner's machine can have `Dockerfile` as its file. The content schema takes the name, and a Dockerfile stage in a lab that runs in the browser is a problem.
- **Tests:** the stage's tests and checks are pytest files, which read the `Dockerfile` in the run's folder and check its instructions. A run needs no Docker.
- **The build:** `pnpm check:machine` builds the image from the stages' solutions with `docker build` where Docker runs Linux containers, which in CI is the lab's Machine labs job on Linux, and fails when it doesn't build.
- **The editor:** shows the solution with Dockerfile highlighting, from CodeMirror's legacy Dockerfile mode.
- **Renovate:** leaves every file in `courses/` alone, as it already did a lab's project, so the images a Dockerfile names move with the lab.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Tests read the Dockerfile, CI builds it on Linux (chosen) | Every learner can run the stage; CI still proves the solution builds | A learner's Dockerfile that passes the tests can still fail to build on their machine |
| Tests that build and run the image | Prove the learner's own image works | Every run needs Docker, which macOS runners lack and Docker Desktop's licence limits; a build pulls base images and takes minutes, past a run's time |
| Hadolint, a Dockerfile linter, as the checker | Rules many teams already use | One more program to pin for six systems; its rules aren't the stage's lesson |
| A given Dockerfile and no stage | Nothing to change | The learner never writes the image |

## Evidence

- Docker's [Dockerfile reference](https://docs.docker.com/reference/dockerfile/): "Docker can build images automatically by reading the instructions from a Dockerfile." Of the shell form of `ENTRYPOINT`: it starts the program "as a subcommand of /bin/sh -c, which does not pass signals. This means that the executable will not be the container's PID 1, and will not receive Unix signals", a property of the file itself that a test can read.
- Docker Desktop's [licence page](https://docs.docker.com/subscription-billing/desktop-license/) (modified 2026-09-28): free for small businesses, "fewer than 250 employees and less than $10 million" in revenue, personal use, education and non-commercial open source; [Docker Engine](https://docs.docker.com/engine/install/) on Linux is under the Apache License 2.0.
- GitHub's [Docker service containers page](https://docs.github.com/en/actions/tutorials/use-containerized-services/use-docker-service-containers): "If your workflows use Docker container actions, job containers, or service containers, then you must use a Linux runner", and "you must use an Ubuntu runner". The runner images' READMEs list no Docker on macOS 15, and Docker 29.7.2 on Windows Server 2025, where it runs Windows containers.
- `@codemirror/legacy-modes` 6.5.5, under the MIT licence, exports `dockerFile` from `mode/dockerfile`, which `StreamLanguage.define` turns into a language the editor highlights.
- Renovate's [Dockerfile manager](https://github.com/renovatebot/renovate/blob/main/lib/modules/manager/dockerfile/index.ts) matches `/(^|/|\.)([Dd]ocker|[Cc]ontainer)file$/`, and [`config:best-practices`](https://github.com/renovatebot/renovate/blob/main/lib/config/presets/internal/config.preset.ts), which `renovate.json` extends, includes `docker:pinDigests`, so without the rule it would open pull requests against a stage's Dockerfile.

## Why

Reading the Dockerfile keeps the stage's runs the same as every other stage's: on any learner's machine, in seconds, with nothing but uv. What a test can't see in the file, that the image builds, CI checks on the one system where GitHub runs Linux containers, so no solution ships that doesn't build. The strongest case against: a learner's Dockerfile can pass every test and still fail to build, which they find only when they run `docker build` themselves.

## Consequences

A Dockerfile stage's tests parse the file in Python, so they test what it says, not what it does. The lab's Machine labs job on Linux pulls the base images the solution names and builds it, which adds minutes to that job. A lab with a Dockerfile stage tells the learner how to build the image if they have Docker or another builder.

## Revisit when

GitHub's macOS or Windows runners run Linux containers, or a lab needs to run the image it builds.

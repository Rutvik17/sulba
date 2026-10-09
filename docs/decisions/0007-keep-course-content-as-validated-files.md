# 7. Keep course content as validated files with permanent ids

- Status: accepted
- Date: 2026-10-08

## Context

Course content has to be reviewable, safe to take from outside contributors, and possible to restructure without losing anyone's progress.

## Decision

Courses are files in this repository: YAML for structure, Markdoc for prose, and real code files for starters, tests and solutions. Every course, module, session, test and review card has a permanent id, and Astro's content collections check every file against a schema at build time.

## Options

| Option | Reviewed in pull requests | Safe for outside contributors | Validated before release |
| --- | --- | --- | --- |
| Markdoc and YAML in the repository (chosen) | Yes | Yes: a closed set of tags, and no code in content | Yes, by schema and by running every solution |
| MDX in the repository | Yes | No: content can import and run any component | Partly |
| A hosted CMS | No: content lives outside Git | Through the CMS's accounts | By the CMS's own rules |
| Content in the database | No | No | Only at run time |

## Evidence

- freeCodeCamp names each challenge file by an id that never changes, and keeps the order in separate files ([freeCodeCamp](https://contribute.freecodecamp.org/how-to-work-on-coding-challenges/)).
- Exercism gives every test case an id: "once a test case has been added, it never changes" ([problem-specifications](https://github.com/exercism/problem-specifications)).
- Stripe built Markdoc because on its old platform "content authoring effectively became software development" ([Stripe](https://stripe.dev/blog/markdoc)).

## Why

Ids kept apart from addresses mean renaming or reordering never loses anyone's progress. Content in Git is open, reviewable, and versioned with the code that renders it.

## Consequences

Writing a session means editing files rather than filling in a form. A scaffolder (`tools/new-session`) creates the files and their ids.

## Revisit when

People who don't use Git need to write content regularly.

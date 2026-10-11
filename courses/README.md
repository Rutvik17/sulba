# Writing a course

A course is a folder of plain files (decision record 7). `pnpm check:content` checks every course on every pull request: each file against its schema, and every stage in Pyodide and in CPython.

## Layout

```text
<course>/
  course.yaml               id, title, and its levels, each with its modules in order
  modules/<module>/
    module.yaml             id, title, and its labs in order
    labs/<lab>/
      lab.yaml              id, title, datasets with their credit, and its stages in order
      data/<file>.csv       each dataset lab.yaml lists
      stages/<stage>/
        stage.yaml          id, kind, title, the file the learner works in, packages, minutes
        brief.md            the task
        hints.md            hints in the order they open, separated by lines of ---
        explanation.md      the explanation
        starter/<file>      the code the stage starts from
        solution/<file>     the learner's file as it should be once the stage is done
        tests/test_*.py     pytest tests, each with @pytest.mark.id and a docstring as its name
```

A folder's name is its address in the URL. Order comes from the YAML files, which must list every folder there is and nothing else. A file the course doesn't use is an error.

## Ids

Every course, level, module, lab, stage and test has a permanent id: a prefix (`crs`, `lvl`, `mod`, `lab`, `stg`, `tst`), an underscore and six lowercase letters or digits, such as `stg_8k2m4q`. Progress is stored against ids, so an id is never changed or reused, even when its folder is renamed or moved.

## Stages

A lab's stages build on each other. A stage's tests run with the lab's data and the earlier stages' solutions. When an earlier stage made the same file, the stage's starter goes below the learner's code.

The checks hold each stage to three things:

- The solution passes every one of the stage's tests, and every earlier stage's.
- The starter fails at least one test.
- Every test has an id no other test has.

Prose is Markdoc, so it takes no HTML or code. It has no tags yet.

## Licence

Course content is all rights reserved ([LICENSE](LICENSE)). Each dataset keeps its own licence, credited in its lab's `lab.yaml`.

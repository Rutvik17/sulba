import { cp, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { pyodideEngine } from '@sulba/lab/node';
import type { RunRequest } from '@sulba/lab/protocol';
import { afterEach, beforeAll, expect, test, vi } from 'vitest';
import { duplicateIds, prove, type Runner, shard } from './check.ts';
import { type Course, loadCourse, type Problem } from './load.ts';

// Each proof runs the fixture course's stages in Pyodide, several runs to a stage.
vi.setConfig({ testTimeout: 60_000 });

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const share = 'demo/modules/counting/labs/tallies/stages/share';
const count = 'demo/modules/counting/labs/tallies/stages/count';
const check = 'demo/modules/counting/labs/tallies/stages/check';
const ship = 'demo/modules/counting/labs/tallies/stages/ship';
const pairs = 'demo/modules/interviews/labs/pairs/stages/pair-sums';
const ledger = 'demo/modules/ledgers/labs/ledger/stages';
const folders: string[] = [];
let runner: Runner;

beforeAll(async () => {
  const engine = await pyodideEngine();
  runner = async (requests) => requests.map(engine.run);
}, 120_000);

afterEach(async () => {
  for (const folder of folders.splice(0)) await rm(folder, { recursive: true, force: true });
});

async function load(root: string, slug = 'demo'): Promise<Course> {
  const { course, problems } = await loadCourse(root, slug);
  if (!course || problems.length) throw new Error(JSON.stringify(problems));
  return course;
}

/**
 * The course's stages proved in Pyodide, as the content check proves them: a lab that runs on the
 * learner's machine runs its stages in CPython alone, in its own project.
 */
function proveInPyodide(course: Course): Promise<Problem[]> {
  const inBrowser = course.levels.flatMap((level) =>
    level.modules.flatMap((module) =>
      module.labs
        .filter((lab) => lab.runs === 'browser')
        .flatMap((lab) => lab.stages.map((stage) => stage.id)),
    ),
  );
  return prove([course], runner, 'Pyodide', new Set(inBrowser));
}

/** The fixture course, with one file's text replaced. */
async function changed(file: string, from: string, to: string): Promise<Course> {
  const root = await mkdtemp(join(tmpdir(), 'sulba-content-'));
  folders.push(root);
  await cp(fixtures, root, { recursive: true });
  const text = await readFile(join(root, file), 'utf8');
  if (!text.includes(from)) throw new Error(`${file} has no "${from}".`);
  await writeFile(join(root, file), text.replace(from, to));
  return load(root);
}

test('every stage of the fixture course that runs in the browser works', async () => {
  expect(await proveInPyodide(await load(fixtures))).toEqual([]);
});

test('a solution that fails a test is a problem', async () => {
  const course = await changed(`${share}/solution/tally.py`, '/ len(choices)', '/ 2');
  // The Catch stage after it uses share too, so its runs fail as well.
  expect(await proveInPyodide(course)).toContainEqual({
    path: share,
    message:
      'Pyodide: The solution fails: "Two of three votes for yes": assert 1.0 == 0.6666666666666666 ± 6.7e-07',
  });
});

test('a starter that already passes is a problem', async () => {
  const course = await changed(
    `${count}/starter/tally.py`,
    'raise NotImplementedError',
    'return sum(1 for each in choices if each == choice)',
  );
  expect(await proveInPyodide(course)).toEqual([
    {
      path: count,
      message: 'Pyodide: The starter passes every test, so the stage asks for nothing.',
    },
  ]);
});

test("a solution that breaks an earlier stage's tests is a problem", async () => {
  const course = await changed(
    `${share}/solution/tally.py`,
    'if each == choice',
    'if each != choice',
  );
  const problems = await proveInPyodide(course);
  expect(problems.map((problem) => problem.message)).toContainEqual(
    expect.stringMatching(/^Pyodide: The solution breaks an earlier stage: "Two votes for yes"/),
  );
});

test('a test without an id is a problem', async () => {
  const course = await changed(
    `${share}/tests/test_tally.py`,
    '@pytest.mark.id("tst_demo03")\n',
    '',
  );
  expect(await proveInPyodide(course)).toEqual([
    {
      path: share,
      message:
        'Pyodide: "Two of three votes for yes" needs an id: @pytest.mark.id("tst_" and 6 letters or digits).',
    },
  ]);
});

test('two tests with one id is a problem', async () => {
  const course = await changed(`${share}/tests/test_tally.py`, 'tst_demo03', 'tst_demo01');
  expect(duplicateIds([course])).toEqual([
    {
      path: `${share}/tests/test_tally.py`,
      message: `The id tst_demo01 is already used by ${count}/tests/test_tally.py.`,
    },
  ]);
});

test("an assistant's test that fails on its own code is a problem", async () => {
  const course = await changed(`${check}/tests/test_report.py`, '== 2', '== 3');
  expect(await proveInPyodide(course)).toContainEqual({
    path: check,
    message: `Pyodide: The assistant's tests must pass on its code, but "One line per choice" fails.`,
  });
});

test("a check that passes on the assistant's code is a problem", async () => {
  const course = await changed(
    `${check}/checks/test_report.py`,
    'assert given == votes()',
    'assert given == given',
  );
  expect(await proveInPyodide(course)).toContainEqual({
    path: check,
    message:
      'Pyodide: "Leaves the list of votes as it was" passes on the assistant\'s code, so it finds no problem.',
  });
});

test("a problem's edit that fixes another problem instead is a problem", async () => {
  const course = await changed(
    `${check}/stage.yaml`,
    'replace: "sorted(set(choices))]"\n      with: "sorted(set(choices), key=lambda each: -share(choices, each))]"',
    'replace: "    choices.sort()\\n"\n      with: ""',
  );
  expect(await proveInPyodide(course)).toEqual([
    {
      path: check,
      message:
        'Pyodide: Fixing "The fewest votes came first" alone doesn\'t pass its check tst_demo06.',
    },
    {
      path: check,
      message:
        'Pyodide: Fixing "The fewest votes came first" alone also passes "Leaves the list of votes as it was": each check must find one problem.',
    },
  ]);
});

test("a Ship stage's solution that fails a check is a problem", async () => {
  const course = await changed(
    `${ship}/solution/report.py`,
    '    return max(set(choices), key=choices.count)',
    '    choices.sort()\n    return max(set(choices), key=choices.count)',
  );
  expect(await proveInPyodide(course)).toEqual([
    {
      path: ship,
      message:
        "Pyodide: The solution fails: \"Leaves the votes as they were\": assert ['no', 'yes', 'yes'] == ['yes', 'no', 'yes']",
    },
  ]);
});

test("a Ship stage's starter that passes every test and check is a problem", async () => {
  const course = await changed(
    `${ship}/starter/report.py`,
    'raise NotImplementedError',
    'return max(set(choices), key=choices.count)',
  );
  expect(await proveInPyodide(course)).toEqual([
    {
      path: ship,
      message: 'Pyodide: The starter passes every test, so the stage asks for nothing.',
    },
  ]);
});

test('two courses that share an id is a problem', async () => {
  const course = await load(fixtures);
  const copy = { ...course, slug: 'copy', id: 'crs_copy01' };
  expect(duplicateIds([course, copy]).map((problem) => problem.message)).toEqual([
    'The id lvl_demo01 is already used by demo/course.yaml (first).',
    'The id mod_demo01 is already used by demo/modules/counting/module.yaml.',
    'The id lab_demo01 is already used by demo/modules/counting/labs/tallies/lab.yaml.',
    `The id stg_demo01 is already used by ${count}/stage.yaml.`,
    `The id crd_demo01 is already used by ${count}/cards.yaml.`,
    `The id crd_demo02 is already used by ${count}/cards.yaml.`,
    `The id tst_demo01 is already used by ${count}/tests/test_tally.py.`,
    `The id tst_demo02 is already used by ${count}/tests/test_tally.py.`,
    `The id stg_demo02 is already used by ${share}/stage.yaml.`,
    `The id crd_demo03 is already used by ${share}/cards.yaml.`,
    `The id tst_demo03 is already used by ${share}/tests/test_tally.py.`,
    `The id stg_demo03 is already used by ${check}/stage.yaml.`,
    `The id tst_demo04 is already used by ${check}/tests/test_report.py.`,
    `The id tst_demo05 is already used by ${check}/tests/test_report.py.`,
    `The id tst_demo06 is already used by ${check}/checks/test_report.py.`,
    `The id tst_demo07 is already used by ${check}/checks/test_report.py.`,
    `The id stg_demo04 is already used by ${ship}/stage.yaml.`,
    `The id tst_demo08 is already used by ${ship}/tests/test_leader.py.`,
    `The id tst_demo10 is already used by ${ship}/tests/test_leader.py.`,
    `The id tst_demo11 is already used by ${ship}/checks/test_leader.py.`,
    `The id tst_demo12 is already used by ${ship}/checks/test_leader.py.`,
    'The id mod_demo02 is already used by demo/modules/interviews/module.yaml.',
    'The id lab_demo02 is already used by demo/modules/interviews/labs/pairs/lab.yaml.',
    `The id stg_demo05 is already used by ${pairs}/stage.yaml.`,
    `The id tst_demo13 is already used by ${pairs}/tests/test_pairs.py.`,
    `The id tst_demo14 is already used by ${pairs}/tests/test_pairs.py.`,
    `The id tst_demo15 is already used by ${pairs}/tests/test_pairs.py.`,
    'The id lvl_demo02 is already used by demo/course.yaml (second).',
    'The id mod_demo03 is already used by demo/modules/ledgers/module.yaml.',
    'The id lab_demo03 is already used by demo/modules/ledgers/labs/ledger/lab.yaml.',
    `The id stg_demo06 is already used by ${ledger}/balance/stage.yaml.`,
    `The id crd_demo04 is already used by ${ledger}/balance/cards.yaml.`,
    `The id tst_demo20 is already used by ${ledger}/balance/tests/test_ledger.py.`,
    `The id tst_demo21 is already used by ${ledger}/balance/tests/test_ledger.py.`,
    `The id tst_demo26 is already used by ${ledger}/balance/tests/test_ledger.py.`,
    `The id stg_demo07 is already used by ${ledger}/audit/stage.yaml.`,
    `The id tst_demo22 is already used by ${ledger}/audit/tests/test_audit.py.`,
    `The id tst_demo23 is already used by ${ledger}/audit/checks/test_audit.py.`,
    `The id stg_demo08 is already used by ${ledger}/close/stage.yaml.`,
    `The id tst_demo24 is already used by ${ledger}/close/tests/test_books.py.`,
    `The id tst_demo25 is already used by ${ledger}/close/checks/test_books.py.`,
  ]);
});

test('the stages are dealt in turn to the parts of a check, each to one', async () => {
  // The tallies lab's four stages, the pairs lab's one, then the ledger lab's three.
  const course = await load(fixtures);
  const ids = (part: number, parts: number) => [...shard([course], part, parts)];
  expect(ids(1, 1)).toEqual([
    'stg_demo01',
    'stg_demo02',
    'stg_demo03',
    'stg_demo04',
    'stg_demo05',
    'stg_demo06',
    'stg_demo07',
    'stg_demo08',
  ]);
  expect(ids(1, 2)).toEqual(['stg_demo01', 'stg_demo03', 'stg_demo05', 'stg_demo07']);
  expect(ids(2, 2)).toEqual(['stg_demo02', 'stg_demo04', 'stg_demo06', 'stg_demo08']);
  expect(ids(3, 4)).toEqual(['stg_demo03', 'stg_demo07']);
});

test('a proof of some stages runs only theirs, each against its earlier stages too', async () => {
  const course = await changed(
    `${count}/starter/tally.py`,
    'raise NotImplementedError',
    'return sum(1 for each in choices if each == choice)',
  );
  const sent: RunRequest[] = [];
  const recording: Runner = (requests) => {
    sent.push(...requests);
    return runner(requests);
  };
  expect(await prove([course], recording, 'Pyodide', new Set(['stg_demo02']))).toEqual([]);
  // The share stage's solution, its starter, and its solution against the count stage's tests.
  expect(sent).toHaveLength(3);
  expect(await prove([course], runner, 'Pyodide', new Set(['stg_demo01']))).toEqual([
    {
      path: count,
      message: 'Pyodide: The starter passes every test, so the stage asks for nothing.',
    },
  ]);
});

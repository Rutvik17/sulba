import { cp, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { pyodideEngine } from '@sulba/lab/node';
import { afterEach, beforeAll, expect, test, vi } from 'vitest';
import { duplicateIds, prove, type Runner } from './check.ts';
import { type Course, loadCourse } from './load.ts';

// Each proof runs the fixture course's stages in Pyodide, several runs to a stage.
vi.setConfig({ testTimeout: 60_000 });

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const share = 'demo/modules/counting/labs/tallies/stages/share';
const count = 'demo/modules/counting/labs/tallies/stages/count';
const check = 'demo/modules/counting/labs/tallies/stages/check';
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

test('every stage of the fixture course works', async () => {
  expect(await prove([await load(fixtures)], runner, 'Pyodide')).toEqual([]);
});

test('a solution that fails a test is a problem', async () => {
  const course = await changed(`${share}/solution/tally.py`, '/ len(choices)', '/ 2');
  // The Catch stage after it uses share too, so its runs fail as well.
  expect(await prove([course], runner, 'Pyodide')).toContainEqual({
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
  expect(await prove([course], runner, 'Pyodide')).toEqual([
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
  const problems = await prove([course], runner, 'Pyodide');
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
  expect(await prove([course], runner, 'Pyodide')).toEqual([
    {
      path: share,
      message:
        'Pyodide: "Two of three votes for yes" needs an id: @pytest.mark.id("tst_" and 6 letters or digits).',
    },
  ]);
});

test('two tests with one id is a problem', async () => {
  const course = await changed(`${share}/tests/test_tally.py`, 'tst_demo03', 'tst_demo01');
  expect(await prove([course], runner, 'Pyodide')).toEqual([
    {
      path: share,
      message: `Pyodide: The test id tst_demo01 is already used by ${count} ("Two votes for yes").`,
    },
  ]);
});

test("an assistant's test that fails on its own code is a problem", async () => {
  const course = await changed(`${check}/tests/test_report.py`, '== 2', '== 3');
  expect(await prove([course], runner, 'Pyodide')).toContainEqual({
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
  expect(await prove([course], runner, 'Pyodide')).toContainEqual({
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
  expect(await prove([course], runner, 'Pyodide')).toEqual([
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

test('two courses that share an id is a problem', async () => {
  const course = await load(fixtures);
  const copy = { ...course, slug: 'copy', id: 'crs_copy01' };
  expect(duplicateIds([course, copy]).map((problem) => problem.message)).toEqual([
    'The id lvl_demo01 is already used by demo/course.yaml (first).',
    'The id mod_demo01 is already used by demo/modules/counting/module.yaml.',
    'The id lab_demo01 is already used by demo/modules/counting/labs/tallies/lab.yaml.',
    `The id stg_demo01 is already used by ${count}/stage.yaml.`,
    `The id stg_demo02 is already used by ${share}/stage.yaml.`,
    `The id stg_demo03 is already used by ${check}/stage.yaml.`,
  ]);
});

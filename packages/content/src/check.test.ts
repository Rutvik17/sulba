import { cp, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { pyodideEngine } from '@sulba/lab/node';
import { afterEach, beforeAll, expect, test } from 'vitest';
import { duplicateIds, prove, type Runner } from './check.ts';
import { type Course, loadCourse } from './load.ts';

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const share = 'demo/modules/counting/labs/tallies/stages/share';
const count = 'demo/modules/counting/labs/tallies/stages/count';
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
  expect(await prove([course], runner, 'Pyodide')).toEqual([
    {
      path: share,
      message:
        'Pyodide: The solution fails: "Two of three votes for yes": assert 1.0 == 0.6666666666666666 ± 6.7e-07',
    },
  ]);
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

test('two courses that share an id is a problem', async () => {
  const course = await load(fixtures);
  const copy = { ...course, slug: 'copy', id: 'crs_copy01' };
  expect(duplicateIds([course, copy]).map((problem) => problem.message)).toEqual([
    'The id lvl_demo01 is already used by demo/course.yaml (first).',
    'The id mod_demo01 is already used by demo/modules/counting/module.yaml.',
    'The id lab_demo01 is already used by demo/modules/counting/labs/tallies/lab.yaml.',
    `The id stg_demo01 is already used by ${count}/stage.yaml.`,
    `The id stg_demo02 is already used by ${share}/stage.yaml.`,
  ]);
});

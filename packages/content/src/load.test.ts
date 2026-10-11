import { cp, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { afterEach, expect, test } from 'vitest';
import { loadCourse } from './load.ts';

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const stages = 'demo/modules/counting/labs/tallies/stages';
const folders: string[] = [];

afterEach(async () => {
  for (const folder of folders.splice(0)) await rm(folder, { recursive: true, force: true });
});

/** A copy of the fixture courses, changed by `change`, then loaded. */
async function loadChanged(change: (root: string) => Promise<void>) {
  const root = await mkdtemp(join(tmpdir(), 'sulba-content-'));
  folders.push(root);
  await cp(fixtures, root, { recursive: true });
  await change(root);
  return loadCourse(root, 'demo');
}

async function edit(path: string, from: string, to: string) {
  const text = await readFile(path, 'utf8');
  if (!text.includes(from)) throw new Error(`${path} has no "${from}".`);
  await writeFile(path, text.replace(from, to));
}

test('the fixture course loads, in the order its files give', async () => {
  const { course, problems } = await loadCourse(fixtures, 'demo');
  expect(problems).toEqual([]);
  const lab = course?.levels[0]?.modules[0]?.labs[0];
  expect(lab?.stages.map((stage) => stage.slug)).toEqual(['count', 'share']);
  expect(lab?.data[0]?.text).toBe('choice\nyes\nno\nyes\n');
  expect(lab?.stages[0]?.hints).toEqual([
    'Compare each choice with the one you are counting.',
    '`sum` adds up a generator of ones.',
  ]);
  expect(Object.keys(lab?.stages[0]?.tests ?? {})).toEqual(['test_tally.py']);
});

test("a stage's version changes when any of its files does", async () => {
  const before = (await loadCourse(fixtures, 'demo')).course?.levels[0]?.modules[0]?.labs[0];
  const { course } = await loadChanged((root) =>
    edit(join(root, stages, 'share/hints.md'), 'Divide', 'Split'),
  );
  const after = course?.levels[0]?.modules[0]?.labs[0];
  expect(after?.stages[0]?.version).toBe(before?.stages[0]?.version);
  expect(after?.stages[1]?.version).not.toBe(before?.stages[1]?.version);
});

test.each([
  {
    name: 'a listed stage that is missing',
    change: (root: string) => rm(join(root, stages, 'share'), { recursive: true }),
    problem: { path: `${stages}/share`, message: 'Listed in lab.yaml but missing.' },
  },
  {
    name: 'a stage folder that is not listed',
    change: (root: string) =>
      cp(join(root, stages, 'share'), join(root, stages, 'extra'), { recursive: true }),
    problem: { path: `${stages}/extra`, message: 'Not listed in lab.yaml.' },
  },
  {
    name: 'a file a stage does not use',
    change: (root: string) => writeFile(join(root, stages, 'count/notes.md'), 'Draft\n'),
    problem: {
      path: `${stages}/count/notes.md`,
      message: 'Not part of the course: list it or remove it.',
    },
  },
  {
    name: 'an id of the wrong kind',
    change: (root: string) =>
      edit(join(root, stages, 'count/stage.yaml'), 'stg_demo01', 'lab_demo09'),
    problem: {
      path: `${stages}/count/stage.yaml`,
      message: 'id: Expected a stage id such as ^stg_[0-9a-z]{6}$',
    },
  },
  {
    name: 'a field the schema does not know',
    change: (root: string) =>
      edit(join(root, stages, 'count/stage.yaml'), 'minutes: 10', 'minutes: 10\nlevel: 2'),
    problem: { path: `${stages}/count/stage.yaml`, message: 'Unrecognized key: "level"' },
  },
  {
    name: 'a tag in prose',
    change: (root: string) =>
      edit(join(root, stages, 'count/brief.md'), 'Write', '{% video /%} Write'),
    problem: { path: `${stages}/count/brief.md`, message: "Undefined tag: 'video'" },
  },
  {
    name: 'an empty hint',
    change: (root: string) =>
      edit(join(root, stages, 'count/hints.md'), '\n---\n', '\n---\n\n---\n'),
    problem: {
      path: `${stages}/count/hints.md`,
      message: 'Each hint, between lines of ---, needs text.',
    },
  },
  {
    name: 'Windows line endings',
    change: (root: string) => writeFile(join(root, stages, 'count/brief.md'), 'Write `count`.\r\n'),
    problem: { path: `${stages}/count/brief.md`, message: 'Use LF line endings.' },
  },
  {
    name: 'a test file named the wrong way',
    change: (root: string) => writeFile(join(root, stages, 'count/tests/checks.py'), ''),
    problem: {
      path: `${stages}/count/tests/checks.py`,
      message: 'A test file is named test_<name>.py.',
    },
  },
  {
    name: 'a starter for a different file',
    change: (root: string) => writeFile(join(root, stages, 'count/starter/other.py'), ''),
    problem: {
      path: `${stages}/count/starter/other.py`,
      message: 'Not part of the course: list it or remove it.',
    },
  },
])('$name is a problem', async ({ change, problem }) => {
  const { problems } = await loadChanged(change);
  expect(problems).toContainEqual(problem);
});

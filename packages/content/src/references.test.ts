import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { expect, test, vi } from 'vitest';
import { type Course, loadCourse } from './load.ts';
import { type Recorder, recordWithUv, referenceProblems } from './references.ts';

// The fixture's make.py installs NumPy with uv the first time it runs.
vi.setConfig({ testTimeout: 120_000 });

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const references = 'demo/modules/counting/labs/tallies/references';

async function load(): Promise<Course> {
  const { course, problems } = await loadCourse(fixtures, 'demo');
  if (!course || problems.length) throw new Error(JSON.stringify(problems));
  return course;
}

/** A recorder that writes these files, whatever make.py would. */
function writing(files: Readonly<Record<string, unknown>>): Recorder {
  return async (_, folder) => {
    for (const [name, value] of Object.entries(files)) {
      await writeFile(join(folder, name), JSON.stringify(value));
    }
  };
}

/** The fixture's recorded poll, with its share changed to `share`. */
function recording(share: number) {
  return { numpy: '2.4.6', polls: [{ choices: ['yes', 'no', 'yes'], choice: 'yes', share }] };
}

test("the fixture's make.py records its references as they are", async () => {
  expect(await referenceProblems(fixtures, [await load()], recordWithUv)).toEqual([]);
});

test('a number made again within 1e-12 of the recorded one agrees with it', async () => {
  const record = writing({ 'shares.json': recording(2 / 3 + 1e-14) });
  expect(await referenceProblems(fixtures, [await load()], record)).toEqual([]);
});

test('a number made again further from the recorded one is a problem', async () => {
  const record = writing({ 'shares.json': recording(0.6666667) });
  expect(await referenceProblems(fixtures, [await load()], record)).toEqual([
    {
      path: `${references}/shares.json`,
      message: 'make.py records polls.0.share as 0.6666667 now, not 0.6666666666666666.',
    },
  ]);
});

test("a reference make.py doesn't record, and a file lab.yaml doesn't list, are problems", async () => {
  const record = writing({ 'votes.json': [] });
  expect(await referenceProblems(fixtures, [await load()], record)).toEqual([
    { path: `${references}/shares.json`, message: "make.py doesn't record this file." },
    {
      path: `${references}/votes.json`,
      message: "make.py records this file, but lab.yaml doesn't list it under references.",
    },
  ]);
});

test('a make.py that stops is a problem, with its error', async () => {
  const record: Recorder = async () => {
    throw new Error('ModuleNotFoundError: No module named torch');
  };
  expect(await referenceProblems(fixtures, [await load()], record)).toEqual([
    {
      path: `${references}/make.py`,
      message: 'It stopped: ModuleNotFoundError: No module named torch',
    },
  ]);
});

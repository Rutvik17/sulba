import { createHash } from 'node:crypto';
import { mkdtemp, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { createServer, type Server } from 'node:http';
import type { AddressInfo } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { holds } from '@sulba/lab/fetched';
import { afterAll, afterEach, beforeAll, expect, test, vi } from 'vitest';
import { type Course, type Lab, loadCourse } from './load.ts';
import { type Recorder, recordWithUv, referenceProblems } from './references.ts';

// The fixture's make.py installs NumPy with uv the first time it runs.
vi.setConfig({ testTimeout: 120_000 });

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const tallies = 'demo/modules/counting/labs/tallies';
const references = `${tallies}/references`;

// A publisher's server, sending the tallies at /tallies.txt and nothing else.
const tallied = new TextEncoder().encode('yes yes no\n');
let server: Server;
let address: string;
const folders: string[] = [];

beforeAll(async () => {
  server = createServer((request, response) => {
    if (request.url === '/tallies.txt') {
      response.writeHead(200, { 'Content-Length': tallied.length }).end(tallied);
    } else {
      response.writeHead(404).end();
    }
  });
  await new Promise<void>((done) => server.listen(0, '127.0.0.1', done));
  address = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
});

afterAll(() => new Promise<void>((done) => server.close(() => done())));

afterEach(async () => {
  for (const folder of folders.splice(0)) await rm(folder, { recursive: true, force: true });
});

/** A new folder for the fetched files, which the test removes. */
async function folder(): Promise<string> {
  const made = await mkdtemp(join(tmpdir(), 'sulba-fetched-'));
  folders.push(made);
  return made;
}

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

/** The fixture course, with its tallies lab fetching the file at `path` from the publisher. */
async function fetching(path: string): Promise<Course> {
  const course = await load();
  const sha256 = createHash('sha256').update(tallied).digest('hex');
  const file = { file: 'tallies.txt', url: `${address}${path}`, bytes: tallied.length, sha256 };
  const licence = { name: 'MIT', url: 'https://opensource.org/license/mit' };
  const source: Lab['fetch'][number] = {
    kind: 'data',
    title: 'Tallies',
    creators: ['A publisher'],
    url: 'https://example.com/tallies',
    licence,
    files: [file],
  };
  const fetches = (lab: Lab): Lab => (lab.references.length ? { ...lab, fetch: [source] } : lab);
  return {
    ...course,
    levels: course.levels.map((level) => ({
      ...level,
      modules: level.modules.map((module) => ({ ...module, labs: module.labs.map(fetches) })),
    })),
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

test("make.py has the lab's data as a run has it: its datasets and the files it fetches", async () => {
  const fetched = await folder();
  const seen: Record<string, string> = {};
  const record: Recorder = async (script, made, data) => {
    for (const name of await readdir(data)) seen[name] = await readFile(join(data, name), 'utf8');
    // A make.py that writes to a file it reads changes only its own copy.
    await writeFile(join(data, 'tallies.txt'), 'no\n');
    await writing({ 'shares.json': recording(2 / 3) })(script, made, data);
  };
  const courses = [await fetching('/tallies.txt')];
  expect(await referenceProblems(fixtures, courses, record, fetched)).toEqual([]);
  expect(seen).toEqual({ 'votes.csv': 'choice\nyes\nno\nyes\n', 'tallies.txt': 'yes yes no\n' });
  const [file] = courses[0]?.levels[0]?.modules[0]?.labs[0]?.fetch[0]?.files ?? [];
  expect(file && (await holds(join(fetched, file.sha256), file))).toBe(true);
});

test("a file make.py reads that can't be fetched is a problem, and make.py doesn't run", async () => {
  const record: Recorder = async () => {
    throw new Error('make.py ran.');
  };
  const courses = [await fetching('/gone.txt')];
  expect(await referenceProblems(fixtures, courses, record, await folder())).toEqual([
    { path: `${tallies}/lab.yaml`, message: `fetch: ${address}/gone.txt answered 404.` },
  ]);
});

import { fileURLToPath } from 'node:url';
import { expect, test } from 'vitest';
import { type Course, type Lab, loadCourse } from './load.ts';
import { canonicalName, lockedIndexes, lockedVersions, projectProblems } from './project-check.ts';

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const lock = 'demo/modules/counting/labs/tallies/project/uv.lock';
// The browser's versions of the packages the fixture project locks.
const pyodide = {
  python: '3.14.2',
  packages: new Map([
    ['iniconfig', '2.3.0'],
    ['packaging', '26.1'],
    ['pluggy', '1.6.0'],
    ['pygments', '2.20.0'],
    ['pytest', '9.0.2'],
    ['pandas', '3.0.2'],
  ]),
};

async function demo(): Promise<Course> {
  const { course, problems } = await loadCourse(fixtures, 'demo');
  if (!course || problems.length) throw new Error(JSON.stringify(problems));
  return course;
}

/** The fixture course with its lab of tallies changed by `change`. */
async function withTallies(change: (lab: Lab) => Lab): Promise<Course> {
  const course = await demo();
  const [level] = course.levels;
  const [counting, ...rest] = level?.modules ?? [];
  if (!level || !counting) throw new Error('The fixture course has no counting module.');
  const [tallies, ...others] = counting.labs;
  if (!tallies) throw new Error('The counting module has no lab of tallies.');
  const changed = { ...counting, labs: [change(tallies), ...others] };
  return { ...course, levels: [{ ...level, modules: [changed, ...rest] }] };
}

/** The fixture course with its lab of ledgers, which runs on the learner's machine, changed. */
async function withLedger(change: (lab: Lab) => Lab): Promise<Course> {
  const course = await demo();
  const [first, second] = course.levels;
  const [ledgers] = second?.modules ?? [];
  const [ledger] = ledgers?.labs ?? [];
  if (!first || !second || !ledgers || !ledger)
    throw new Error('The fixture course has no ledger.');
  const changed = { ...ledgers, labs: [change(ledger)] };
  return { ...course, levels: [first, { ...second, modules: [changed] }] };
}

const ledgerLock = 'demo/modules/ledgers/labs/ledger/project/uv.lock';

/** A lock's entries for torch from an index, as uv writes them for macOS and for the rest. */
function torchFrom(index: string): string {
  return ['2.14.1', '2.14.1+cpu']
    .map(
      (version) =>
        `[[package]]\nname = "torch"\nversion = "${version}"\nsource = { registry = "${index}" }\n`,
    )
    .join('\n');
}

const withTorch = (index: string) => (lab: Lab) => ({
  ...lab,
  project: { ...lab.project, 'uv.lock': `${lab.project['uv.lock'] ?? ''}\n${torchFrom(index)}` },
  stages: lab.stages.map((stage, at) =>
    at === 0 ? { ...stage, packages: ['torch' as const] } : stage,
  ),
});

const relock = (from: string, to: string) => (lab: Lab) => {
  const text = lab.project['uv.lock'] ?? '';
  if (!text.includes(from)) throw new Error(`The lock has no "${from}".`);
  return { ...lab, project: { ...lab.project, 'uv.lock': text.replace(from, to) } };
};

test('names compare as the standards compare them', () => {
  expect(canonicalName('Jinja2')).toBe('jinja2');
  expect(canonicalName('pydantic_core')).toBe('pydantic-core');
  expect(canonicalName('zope..Interface')).toBe('zope-interface');
});

test('a lock gives every version it pins of each package', () => {
  const text = [
    '[[package]]\nname = "numpy"\nversion = "2.4.6"\n',
    '[[package]]\nname = "Pygments"\nversion = "2.20.0"\n',
    '[[package]]\nname = "numpy"\nversion = "2.2.6"\n',
  ].join('\n');
  expect(lockedVersions(text)).toEqual(
    new Map([
      ['numpy', ['2.4.6', '2.2.6']],
      ['pygments', ['2.20.0']],
    ]),
  );
});

test("the fixture project locks the browser's versions", async () => {
  expect(projectProblems([await demo()], pyodide)).toEqual([]);
});

test('a package locked at another version than the browser runs is a problem', async () => {
  const course = await withTallies(
    relock('name = "pluggy"\nversion = "1.6.0"', 'name = "pluggy"\nversion = "1.5.0"'),
  );
  expect(projectProblems([course], pyodide)).toEqual([
    { path: lock, message: 'pluggy is locked at 1.5.0, but the browser runs 1.6.0.' },
  ]);
});

test("a project on another Python than the browser's is a problem", async () => {
  const course = await withTallies(
    relock('requires-python = "==3.14.*"', 'requires-python = ">=3.12"'),
  );
  expect(projectProblems([course], pyodide)).toEqual([
    {
      path: lock,
      message: 'requires-python is >=3.12, but the browser runs Python 3.14.2: make it ==3.14.*.',
    },
  ]);
});

test("a package the lab's stages load must be locked", async () => {
  const course = await withTallies((lab) => ({
    ...lab,
    stages: lab.stages.map((stage, index) =>
      index === 1 ? { ...stage, packages: ['pandas'] } : stage,
    ),
  }));
  expect(projectProblems([course], pyodide)).toEqual([
    { path: lock, message: "pandas isn't locked, but the lab's stages load it." },
  ]);
});

test('a lab without a project has nothing to check', async () => {
  const course = await withTallies((lab) => ({ ...lab, project: {} }));
  expect(projectProblems([course], { python: '3.13.0', packages: new Map() })).toEqual([]);
});

test('a lock gives the index each package comes from', () => {
  expect(lockedIndexes(torchFrom('https://download.pytorch.org/whl/cpu'))).toEqual(
    new Map([
      ['torch', ['https://download.pytorch.org/whl/cpu', 'https://download.pytorch.org/whl/cpu']],
    ]),
  );
});

test("a machine lab holds pytest to the browser's version, and leaves the rest to its resolver", async () => {
  // The lab of ledgers locks pluggy, pytest's own dependency, at another version than the browser's.
  expect(projectProblems([await demo()], pyodide)).toEqual([]);
  const course = await withLedger(
    relock('name = "pytest"\nversion = "9.0.2"', 'name = "pytest"\nversion = "9.0.1"'),
  );
  expect(projectProblems([course], pyodide)).toEqual([
    { path: ledgerLock, message: 'pytest is locked at 9.0.1, but the browser runs 9.0.2.' },
  ]);
});

test("a machine lab installs torch from PyTorch's CPU index", async () => {
  const fromIndex = await withLedger(withTorch('https://download.pytorch.org/whl/cpu'));
  expect(projectProblems([fromIndex], pyodide)).toEqual([]);
  const fromPyPI = await withLedger(withTorch('https://pypi.org/simple'));
  const message =
    'torch is locked from https://pypi.org/simple, but a machine lab installs it from https://download.pytorch.org/whl/cpu.';
  expect(projectProblems([fromPyPI], pyodide)).toEqual([
    { path: ledgerLock, message },
    { path: ledgerLock, message },
  ]);
});

test('a machine lab installs its other machine packages from PyPI', async () => {
  const course = await withLedger((lab) => ({
    ...lab,
    project: {
      ...lab.project,
      'uv.lock': `${lab.project['uv.lock'] ?? ''}\n[[package]]\nname = "tokenizers"\nversion = "0.23.3"\nsource = { registry = "https://pypi.org/simple" }\n`,
    },
    stages: lab.stages.map((stage, at) =>
      at === 0 ? { ...stage, packages: ['tokenizers' as const] } : stage,
    ),
  }));
  expect(projectProblems([course], pyodide)).toEqual([]);
});

test("a machine lab's runner needs pytest", async () => {
  const course = await withLedger(
    relock('[[package]]\nname = "pytest"', '[[package]]\nname = "pytest-renamed"'),
  );
  expect(projectProblems([course], pyodide)).toEqual([
    {
      path: ledgerLock,
      message: "pytest isn't locked, but the runner in the lab's download runs the tests with it.",
    },
  ]);
});

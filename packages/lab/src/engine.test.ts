// The fixtures run in Pyodide here and in CPython in python/tests, against the same expected
// results, so the browser and a learner's machine report every run the same way.
import { readdir, readFile } from 'node:fs/promises';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { beforeAll, expect, test } from 'vitest';
import { shares } from './chart.fixture.ts';
import type { Engine } from './engine.ts';
import { counted } from './figures.fixture.ts';
import { pyodideEngine } from './node.ts';
import { importNames, pythonPackages, type RunResult } from './protocol.ts';

const fixtures = fileURLToPath(new URL('../fixtures/', import.meta.url));

async function session(name: string) {
  const folder = join(fixtures, name);
  const files: Record<string, string> = {};
  for (const entry of await readdir(folder, { recursive: true, withFileTypes: true })) {
    if (!entry.isFile() || entry.name === 'expected.json') continue;
    const path = join(entry.parentPath, entry.name);
    files[relative(folder, path).split(sep).join('/')] = await readFile(path, 'utf8');
  }
  const tests = Object.keys(files)
    .filter((path) => path.startsWith('tests/'))
    .sort();
  return { files, tests, packages: pythonPackages };
}

function withoutTimes({ status: _, durationMs: __, tests, ...rest }: RunResult) {
  return { ...rest, tests: tests.map(({ durationMs: _, ...test }) => test) };
}

let engine: Engine;

beforeAll(async () => {
  engine = await pyodideEngine();
}, 120_000);

// First in the file: a run that imports a package would leave it imported for later runs.
test('packages are imported as they load, so a run never waits for an import', () => {
  const names = JSON.stringify(pythonPackages.map((name) => importNames[name]));
  const test = `import sys\n\n\ndef test_imported():\n    assert [name for name in ${names} if name not in sys.modules] == []\n`;
  const result = engine.run({
    files: { 'tests/test_imported.py': test },
    tests: ['tests/test_imported.py'],
    packages: pythonPackages,
  });
  expect(result.status).toBe('pass');
});

test.each((await readdir(fixtures)).sort())('%s gives its expected result', async (name) => {
  const expected = JSON.parse(await readFile(join(fixtures, name, 'expected.json'), 'utf8'));
  expect(withoutTimes(engine.run(await session(name)))).toEqual(expected);
});

test('a run adds up its tests', async () => {
  expect(engine.run(await session('passes')).status).toBe('pass');
  expect(engine.run(await session('fails')).status).toBe('fail');
  expect(engine.run(await session('syntax-error')).status).toBe('error');
});

test('a second run uses the new code', async () => {
  const request = await session('fails');
  const first = engine.run(request);
  const files = {
    ...request.files,
    'stats.py': request.files['stats.py']?.replace('return sum(values)', 'return 2 * sum(values)'),
  } as Record<string, string>;
  const second = engine.run({ ...request, files });
  expect(first.tests.map((test) => test.status)).toEqual(['pass', 'fail', 'error']);
  expect(second.tests.map((test) => test.status)).toEqual(['fail', 'fail', 'error']);
});

test("figures are the strings a stage's figures.py returns, read from the lab's data", () => {
  expect(engine.figures(counted)).toEqual({
    figures: { yes: '2', share: '0.6667' },
    problem: null,
  });
});

test('figures that fail give the error', () => {
  const files = { 'figures.py': 'def figures():\n    return {"x": str(1 / 0)}\n' };
  expect(engine.figures(files)).toEqual({
    figures: null,
    problem: 'ZeroDivisionError: division by zero',
  });
});

test("a chart is what a stage's chart.py draws with the learner's code and the values", () => {
  expect(engine.chart(shares)).toEqual({
    chart: {
      x: { min: 0, max: 1, step: 1, label: 'votes' },
      y: { min: 0, max: 1, step: 0.5, label: 'share' },
      lines: [{ style: 'main', label: 'Yes', x: [0, 1], y: [0, 0.6666666666666666] }],
      points: [{ x: 1, y: 0.6666666666666666 }],
      readouts: [{ label: 'share of 3', value: '0.6667' }],
      description: 'The share of yes votes in the first 3',
    },
    problem: null,
  });
});

test('a chart that fails gives the error', () => {
  expect(engine.chart({ ...shares, values: { votes: 0 } })).toEqual({
    chart: null,
    problem: { kind: 'ZeroDivisionError', message: 'division by zero' },
  });
});

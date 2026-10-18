// Every fixture, run in Pyodide and in CPython through runInCPython, gives the same result. CPython
// needs uv, which CI has; a machine without it skips this file.
import { spawnSync } from 'node:child_process';
import { readdir, readFile } from 'node:fs/promises';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { expect, test } from 'vitest';
import { shares } from './chart.fixture.ts';
import { counted } from './figures.fixture.ts';
import {
  chartsInCPython,
  figuresInCPython,
  projectRuntime,
  pyodideEngine,
  runEachInCPython,
  runInCPython,
} from './node.ts';
import { pythonPackages, type RunRequest, type RunResult } from './protocol.ts';

const hasUv = spawnSync('uv', ['--version']).status === 0;
const fixtures = fileURLToPath(new URL('../fixtures/', import.meta.url));

async function request(name: string): Promise<RunRequest> {
  const folder = join(fixtures, name);
  const files: Record<string, string> = {};
  for (const entry of await readdir(folder, { recursive: true, withFileTypes: true })) {
    if (!entry.isFile() || entry.name === 'expected.json') continue;
    const path = join(entry.parentPath, entry.name);
    files[relative(folder, path).split(sep).join('/')] = await readFile(path, 'utf8');
  }
  const tests = Object.keys(files).filter((path) => path.startsWith('tests/'));
  return { files, tests: tests.sort(), packages: pythonPackages };
}

function withoutTimes({ durationMs: _, tests, ...rest }: RunResult) {
  return { ...rest, tests: tests.map(({ durationMs: __, ...each }) => each) };
}

test.skipIf(!hasUv)(
  'CPython and Pyodide give the same result for every fixture',
  async () => {
    const requests = await Promise.all((await readdir(fixtures)).sort().map(request));
    const engine = await pyodideEngine();
    const inPyodide = requests.map(engine.run).map(withoutTimes);
    const inCPython = (await runInCPython(requests)).map(withoutTimes);
    expect(inCPython).toEqual(inPyodide);
  },
  180_000,
);

test.skipIf(!hasUv)(
  'CPython and Pyodide give the same figures',
  async () => {
    const engine = await pyodideEngine();
    expect(await figuresInCPython([counted])).toEqual([engine.figures(counted)]);
  },
  180_000,
);

test.skipIf(!hasUv)(
  'CPython and Pyodide draw the same chart',
  async () => {
    const engine = await pyodideEngine();
    const requests = [shares, { ...shares, values: { votes: 0 } }];
    expect(await chartsInCPython(requests)).toEqual(requests.map(engine.chart));
  },
  180_000,
);

test("a machine lab's runtime changes with the files it fetches", async () => {
  const lock = 'version = 1\n';
  const tiles = { url: 'https://example.com/tiles.bin', bytes: 1024, sha256: 'a'.repeat(64) };
  const plain = await projectRuntime(lock);
  expect(await projectRuntime(lock, {})).toBe(plain);
  const fetching = await projectRuntime(lock, { 'data/tiles.bin': tiles });
  expect(fetching).not.toBe(plain);
  const changed = { 'data/tiles.bin': { ...tiles, sha256: 'b'.repeat(64) } };
  expect(await projectRuntime(lock, changed)).not.toBe(fetching);
});

test.skipIf(!hasUv)(
  'a run that never ends is stopped, and the next one still runs',
  async () => {
    const passes = await request('passes');
    const endless = {
      ...passes,
      files: { ...passes.files, 'stats.py': 'while True:\n    pass\n' },
    };
    const [stopped, ran] = await runEachInCPython([endless, passes], 10_000);
    expect(stopped?.problem).toEqual({
      kind: 'TimeLimit',
      message: 'Stopped after 10 seconds.',
      location: null,
    });
    expect(ran?.status).toBe('pass');
  },
  60_000,
);

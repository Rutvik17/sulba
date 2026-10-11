// A learner's machine and the browser must run the same Python packages, so every package
// pinned for CPython (python/uv.lock) must be the version Pyodide ships.
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { expect, test } from 'vitest';
import { pyodideVersion, pythonPackages } from './protocol.ts';

const lock = JSON.parse(
  await readFile(createRequire(import.meta.url).resolve('pyodide/pyodide-lock.json'), 'utf8'),
) as { info: { python: string }; packages: Record<string, { version: string }> };
const uvLock = await readFile(new URL('../python/uv.lock', import.meta.url), 'utf8');
const pinned = new Map(
  [...uvLock.matchAll(/\[\[package\]\]\nname = "([^"]+)"\nversion = "([^"]+)"/g)].map(
    ([, name, version]) => [name as string, version as string],
  ),
);

test('CPython runs the Python version Pyodide ships', () => {
  expect(uvLock).toContain(`requires-python = "==${lock.info.python}"`);
});

test('every package served to the browser is pinned for CPython', () => {
  for (const name of ['pytest', ...pythonPackages]) expect(pinned.has(name), name).toBe(true);
});

test('every package in both has the same version', () => {
  const shared = [...pinned].filter(([name]) => name in lock.packages);
  expect(shared.length).toBeGreaterThan(0);
  for (const [name, version] of shared) expect(version, name).toBe(lock.packages[name]?.version);
});

test('the site serves the Pyodide release the npm package holds', async () => {
  const { version } = JSON.parse(
    await readFile(createRequire(import.meta.url).resolve('pyodide/package.json'), 'utf8'),
  ) as { version: string };
  expect(pyodideVersion).toBe(version);
});

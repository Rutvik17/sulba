import { mkdtemp, readdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import type { Figures, RunRequest } from '@sulba/lab/protocol';
import { expect, test } from 'vitest';
import { cachedFigures, figuresKey } from './figures-cache';

/** A runner that answers each set of files with its figures.py's length, and counts what it ran. */
function counting(problem: string | null = null) {
  const ran: RunRequest['files'][] = [];
  const runner = async (fileSets: readonly RunRequest['files'][]): Promise<Figures[]> => {
    ran.push(...fileSets);
    return fileSets.map((files) => ({
      figures: problem ? null : { length: String(files['figures.py']?.length) },
      problem,
    }));
  };
  return { ran, runner };
}

const one = { 'figures.py': 'def figures(): ...', 'data/a.csv': 'x\n1\n' };
const two = { 'figures.py': 'def figures(): return {}', 'data/a.csv': 'x\n1\n' };

test('figures are computed once, and read back after for the same files and runtime', async () => {
  const folder = await mkdtemp(join(tmpdir(), 'figures-'));
  const first = counting();
  const computed = await cachedFigures(folder, 'r1', first.runner)([one, two]);
  expect(first.ran).toEqual([one, two]);
  const second = counting();
  const kept = await cachedFigures(folder, 'r1', second.runner)([one, two]);
  expect(second.ran).toEqual([]);
  expect(kept).toEqual(computed);
});

test('only the sets of files not kept are computed, and the answers keep their order', async () => {
  const folder = await mkdtemp(join(tmpdir(), 'figures-'));
  await cachedFigures(folder, 'r1', counting().runner)([two]);
  const later = counting();
  const answers = await cachedFigures(folder, 'r1', later.runner)([one, two]);
  expect(later.ran).toEqual([one]);
  expect(answers.map(({ figures }) => figures?.length)).toEqual(['18', '24']);
});

test('a changed file or another runtime computes the figures again', async () => {
  const folder = await mkdtemp(join(tmpdir(), 'figures-'));
  await cachedFigures(folder, 'r1', counting().runner)([one]);
  const edited = { ...one, 'data/a.csv': 'x\n2\n' };
  const again = counting();
  await cachedFigures(folder, 'r1', again.runner)([edited]);
  await cachedFigures(folder, 'r2', again.runner)([one]);
  expect(again.ran).toEqual([edited, one]);
});

test('figures that failed are not kept', async () => {
  const folder = await mkdtemp(join(tmpdir(), 'figures-'));
  const failing = counting('NameError: x');
  const [answer] = await cachedFigures(folder, 'r1', failing.runner)([one]);
  expect(answer?.problem).toBe('NameError: x');
  expect(await readdir(folder)).toEqual([]);
});

test('a kept file that cannot be read is computed again', async () => {
  const folder = await mkdtemp(join(tmpdir(), 'figures-'));
  await writeFile(join(folder, `${figuresKey(one, 'r1')}.json`), '{"figures":');
  const again = counting();
  const [answer] = await cachedFigures(folder, 'r1', again.runner)([one]);
  expect(again.ran).toEqual([one]);
  expect(answer?.figures).toEqual({ length: '18' });
});

test("the key doesn't depend on the order the files come in", () => {
  const reversed = Object.fromEntries(Object.entries(one).reverse());
  expect(figuresKey(reversed, 'r1')).toBe(figuresKey(one, 'r1'));
  expect(figuresKey(one, 'r2')).not.toBe(figuresKey(one, 'r1'));
});

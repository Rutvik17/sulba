import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import init, { type Diagnostic, PositionEncoding, Workspace } from '@astral-sh/ruff-wasm-web';
import { Text } from '@codemirror/state';
import { beforeAll, expect, test } from 'vitest';
import { ruffSettings, toDiagnostics } from './ruff-settings.ts';

let ruff: Workspace;

beforeAll(async () => {
  const wasm = createRequire(import.meta.url).resolve('@astral-sh/ruff-wasm-web/ruff_wasm_bg.wasm');
  await init({ module_or_path: await readFile(wasm) });
  ruff = new Workspace(ruffSettings, PositionEncoding.Utf16);
});

function check(code: string) {
  const doc = Text.of(code.split('\n'));
  return toDiagnostics(doc, ruff.check(code) as Diagnostic[]).map((found) => ({
    ...found,
    text: doc.sliceString(found.from, found.to),
  }));
}

test('a name Python cannot find is an error, marked where it is used', () => {
  expect(check('def f(x):\n    return y + x\n')).toEqual([
    {
      from: 21,
      to: 22,
      severity: 'error',
      message: 'Undefined name `y`',
      source: 'F821',
      text: 'y',
    },
  ]);
});

test('positions count characters as the editor does, past an emoji', () => {
  const [found] = check('s = "é😀" + z\n');
  expect(found?.text).toBe('z');
});

test('an unused import is a hint, marked with its own class', () => {
  expect(check('import os\n')).toEqual([
    {
      from: 7,
      to: 9,
      severity: 'hint',
      message: '`os` imported but unused',
      source: 'F401',
      markClass: 'cm-lintRange-unnecessary',
      text: 'os',
    },
  ]);
});

test('a syntax error is an error, with no rule code', () => {
  const [found] = check('def f(:\n    pass\n');
  expect(found).toMatchObject({ severity: 'error', text: ':' });
  expect(found).not.toHaveProperty('source');
});

test('a statement mistake is a warning', () => {
  expect(check('x = 1; y = 2\n')).toMatchObject([{ severity: 'warning', source: 'E702' }]);
});

test('Ruff formats in its default style', () => {
  expect(ruff.format('x = [1,2,\n3]\ndef f( a ):\n  return a\n')).toBe(
    'x = [1, 2, 3]\n\n\ndef f(a):\n    return a\n',
  );
});

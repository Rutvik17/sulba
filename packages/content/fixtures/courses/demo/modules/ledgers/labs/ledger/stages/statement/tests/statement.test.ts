import assert from 'node:assert/strict';
import { test } from 'node:test';
import { statement } from '#statement.ts';

test('tst_demo27 Shows each entry with its sign', () => {
  assert.deepEqual(statement([12, -5]).slice(0, 2), ['+12', '-5']);
});

test('tst_demo28 Ends with the balance', () => {
  assert.equal(statement([12, -5, 30]).at(-1), '= 37');
});

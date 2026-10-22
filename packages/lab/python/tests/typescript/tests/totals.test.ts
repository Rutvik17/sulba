import assert from 'node:assert/strict';
import { test } from 'node:test';
import { dollars, total } from '#totals.ts';

test('tst_ts0001 Adds the amounts', () => {
  console.log('Adding 2 amounts.');
  assert.equal(total([1250, 300]), 1550);
});

test('tst_ts0002 Shows dollars and cents', () => {
  assert.deepEqual([dollars(1550), dollars(5)], ['15.50', '0.5']);
});

test('tst_ts0003 Rounds part of a cent', () => {
  assert.equal(dollars(0.5), '0.01');
});

test('A test without an id', () => {
  assert.equal(total([]), 0);
});

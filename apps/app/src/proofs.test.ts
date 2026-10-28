import type { CriterionProof } from '@sulba/data/evidence';
import { expect, test } from 'vitest';
import { reasonOf, specProofText } from './proofs';

const proof = (change: Partial<CriterionProof>): CriterionProof => ({
  criterionId: 'c1',
  specId: 's1',
  specNumber: 3,
  specTitle: 'Retry failed payments',
  specStatus: 'approved',
  criterionNumber: 1,
  text: 'Retries once after 30 seconds',
  state: 'unproven',
  tests: 0,
  passed: 0,
  failed: 0,
  skipped: 0,
  suspectSince: null,
  checkedAt: null,
  ...change,
});

test('a criterion’s proof says which tests it comes from', () => {
  expect(reasonOf(proof({ state: 'proven', tests: 1, passed: 1 }))).toBe(
    '1 test names it, and it passed',
  );
  expect(reasonOf(proof({ state: 'proven', tests: 3, passed: 3 }))).toBe(
    '3 tests name it, and all of them passed',
  );
  expect(reasonOf(proof({ state: 'failing', tests: 2, passed: 1, failed: 1 }))).toBe(
    '1 of the 2 tests that name it failed',
  );
  expect(reasonOf(proof({}))).toBe('No test in the latest runs names it');
  expect(reasonOf(proof({ tests: 2, passed: 1, skipped: 1 }))).toBe(
    '1 of the 2 tests that name it skipped',
  );
  expect(reasonOf(proof({ tests: 1, passed: 1, suspectSince: '2026-10-28T09:00:00Z' }))).toBe(
    'Reworded since its tests ran. Confirm they check the new wording to count them again',
  );
});

test('a spec’s proof puts failing criteria first', () => {
  expect(specProofText(undefined)).toBe('No criteria');
  expect(specProofText({ criteria: 0, proven: 0, failing: 0 })).toBe('No criteria');
  expect(specProofText({ criteria: 3, proven: 2, failing: 0 })).toBe('2 of 3 proven');
  expect(specProofText({ criteria: 3, proven: 1, failing: 1 })).toBe('1 failing');
});

import { strFromU8, unzipSync } from 'fflate';
import { expect, test } from 'vitest';
import { zipped } from './download';

test('a download holds each file inside one folder, with its text', () => {
  const files = unzipSync(
    zipped('tallies', {
      'tally.py': 'def count():\n    pass\n',
      'data/votes.csv': 'choice\nyes\n',
    }),
  );
  expect(Object.keys(files).sort()).toEqual(['tallies/data/votes.csv', 'tallies/tally.py']);
  expect(strFromU8(files['tallies/tally.py'] ?? new Uint8Array())).toBe('def count():\n    pass\n');
});

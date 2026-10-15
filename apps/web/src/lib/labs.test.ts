import { fileURLToPath } from 'node:url';
import { loadCourse } from '@sulba/content';
import { expect, test } from 'vitest';
import { labEntries } from './labs';

const fixtures = fileURLToPath(
  new URL('../../../../packages/content/fixtures/courses', import.meta.url),
);

test('a dataset keeps its own page for the credit, and is served at an address named for its text', async () => {
  const { course } = await loadCourse(fixtures, 'demo');
  if (!course) throw new Error('The fixture course should load.');
  const [lab] = labEntries(course);

  expect(lab?.data).toEqual([
    expect.objectContaining({
      file: 'votes.csv',
      url: 'https://example.com/votes',
      path: 'data/votes.csv',
      served: expect.stringMatching(/^\/data\/[0-9a-f]{16}\/votes\.csv$/),
    }),
  ]);
  expect(Object.keys(lab?.files ?? {})).toEqual(['data/votes.csv']);
});

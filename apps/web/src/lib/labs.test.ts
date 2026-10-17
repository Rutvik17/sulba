import { fileURLToPath } from 'node:url';
import { type Course, loadCourse } from '@sulba/content';
import { expect, test } from 'vitest';
import { labEntries } from './labs';

const fixtures = fileURLToPath(
  new URL('../../../../packages/content/fixtures/courses', import.meta.url),
);

/** The fixture course: one level, with one module, with the lab Tallies. */
async function demo(): Promise<Course> {
  const { course } = await loadCourse(fixtures, 'demo');
  if (!course) throw new Error('The fixture course should load.');
  return course;
}

test('a dataset keeps its own page for the credit, and is served at an address named for its text', async () => {
  const [lab] = labEntries(await demo());

  expect(lab?.data).toEqual([
    expect.objectContaining({
      file: 'votes.csv',
      url: 'https://example.com/votes',
      path: 'data/votes.csv',
      served: expect.stringMatching(/^\/data\/[0-9a-f]{16}\/votes\.csv$/),
    }),
  ]);
});

test("a lab's references are served apart from its page, at addresses named for their text", async () => {
  const [lab] = labEntries(await demo());

  expect(lab?.references).toEqual([
    {
      path: 'references/shares.json',
      served: expect.stringMatching(/^\/references\/[0-9a-f]{16}\/shares\.json$/),
    },
  ]);
  expect(Object.keys(lab?.files ?? {})).toEqual(['data/votes.csv', 'references/shares.json']);
});

test("a lab's project files are served apart from its page, at addresses named for their text", async () => {
  const [lab] = labEntries(await demo());

  expect(lab?.project).toEqual([
    { name: 'README.md', served: expect.stringMatching(/^\/project\/[0-9a-f]{16}\/README\.md$/) },
    {
      name: 'pyproject.toml',
      served: expect.stringMatching(/^\/project\/[0-9a-f]{16}\/pyproject\.toml$/),
    },
    { name: 'uv.lock', served: expect.stringMatching(/^\/project\/[0-9a-f]{16}\/uv\.lock$/) },
  ]);
  expect(lab?.projectFiles['pyproject.toml']).toMatch(/^\[project\]\n/);
});

test("each lab's order counts the course's labs through its levels and modules", async () => {
  const course = await demo();
  const level = course.levels[0];
  const module = level?.modules[0];
  const lab = module?.labs[0];
  if (!level || !module || !lab) throw new Error('The fixture course should have a lab.');
  const more = { ...module, slug: 'more', labs: [lab, { ...lab, slug: 'again' }] };
  const next = { ...level, slug: 'second', modules: [{ ...module, slug: 'last' }] };

  const entries = labEntries({ ...course, levels: [{ ...level, modules: [module, more] }, next] });

  expect(entries.map(({ path, order }) => [path, order])).toEqual([
    ['demo/counting/tallies', 0],
    ['demo/more/tallies', 1],
    ['demo/more/again', 2],
    ['demo/last/tallies', 3],
  ]);
});

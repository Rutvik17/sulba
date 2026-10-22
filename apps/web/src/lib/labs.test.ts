import { fileURLToPath } from 'node:url';
import { type Course, loadCourse } from '@sulba/content';
import { expect, test } from 'vitest';
import { labEntries } from './labs';

const fixtures = fileURLToPath(
  new URL('../../../../packages/content/fixtures/courses', import.meta.url),
);

/** The fixture course, whose first lab is Tallies and whose last, Ledger, runs on the machine. */
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

test("a machine lab's download carries the runner and the files the lab gives, each served under its own name", async () => {
  const runner = { 'sulba.py': '# the runner\n', '.sulba/sulba_runner.py': '# its module\n' };
  const entries = labEntries(await demo(), new Map(), runner);
  const ledger = entries.find((entry) => entry.path === 'demo/ledgers/ledger');
  expect(ledger?.runs).toBe('machine');
  expect(ledger?.project.map(({ name }) => name)).toEqual([
    'README.md',
    'pyproject.toml',
    'uv.lock',
    'entries.py',
    'sulba.py',
    '.sulba/sulba_runner.py',
  ]);
  expect(ledger?.given).toEqual(['entries.py']);
  expect(ledger?.projectFiles['entries.py']).toContain('def amounts() -> list[int]:');
  expect(ledger?.project.at(-1)?.served).toMatch(/^\/project\/[0-9a-f]{16}\/sulba_runner\.py$/);
  expect(ledger?.projectFiles['.sulba/sulba_runner.py']).toBe('# its module\n');
  const tallies = entries.find((entry) => entry.path === 'demo/counting/tallies');
  expect(tallies?.runs).toBe('browser');
  expect(tallies?.project.map(({ name }) => name)).toEqual([
    'README.md',
    'pyproject.toml',
    'uv.lock',
  ]);
});

test("a machine lab's entry carries what it fetches, with each source's credit", async () => {
  const ledger = labEntries(await demo()).find((entry) => entry.path === 'demo/ledgers/ledger');
  expect(ledger?.fetch.map(({ kind, title }) => [kind, title])).toEqual([
    ['data', 'Fashion-MNIST'],
  ]);
  expect(ledger?.fetch[0]?.files.map(({ file, bytes }) => [file, bytes])).toEqual([
    ['t10k-labels-idx1-ubyte.gz', 5148],
  ]);
  // The site serves none of them.
  expect(Object.keys(ledger?.files ?? {})).toEqual(['data/entries.csv', 'entries.py']);
});

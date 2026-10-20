import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { afterEach, expect, test } from 'vitest';
import { courseSlugs, loadCourse } from './load.ts';

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const stages = 'demo/modules/counting/labs/tallies/stages';
const project = 'demo/modules/counting/labs/tallies/project';
const references = 'demo/modules/counting/labs/tallies/references';
const folders: string[] = [];

afterEach(async () => {
  for (const folder of folders.splice(0)) await rm(folder, { recursive: true, force: true });
});

/** A copy of the fixture courses, changed by `change`, then loaded. */
async function loadChanged(change: (root: string) => Promise<void>) {
  const root = await mkdtemp(join(tmpdir(), 'sulba-content-'));
  folders.push(root);
  await cp(fixtures, root, { recursive: true });
  await change(root);
  return loadCourse(root, 'demo');
}

async function edit(path: string, from: string, to: string) {
  const text = await readFile(path, 'utf8');
  if (!text.includes(from)) throw new Error(`${path} has no "${from}".`);
  await writeFile(path, text.replace(from, to));
}

test('the fixture course loads, in the order its files give', async () => {
  const { course, problems } = await loadCourse(fixtures, 'demo');
  expect(problems).toEqual([]);
  const lab = course?.levels[0]?.modules[0]?.labs[0];
  expect(lab?.stages.map((stage) => stage.slug)).toEqual(['count', 'share', 'check', 'ship']);
  expect(lab?.data[0]?.text).toBe('choice\nyes\nno\nyes\n');
  expect(lab?.references.map(({ file }) => file)).toEqual(['shares.json']);
  expect(JSON.parse(lab?.references[0]?.text ?? '')).toMatchObject({ numpy: '2.4.6' });
  expect(lab?.code.map(({ title, licence }) => [title, licence.name])).toEqual([
    ['tally.js 1.0.0', 'MIT'],
  ]);
  expect(Object.keys(lab?.project ?? {})).toEqual(['README.md', 'pyproject.toml', 'uv.lock']);
  expect(lab?.project['pyproject.toml']).toMatch(/^\[project\]\nname = "tallies"\n/);
  expect(lab?.stages[0]?.hints).toEqual([
    'Compare each choice with the one you are counting.',
    '`sum` adds up a generator of ones.',
  ]);
  expect(Object.keys(lab?.stages[0]?.tests ?? {})).toEqual(['test_tally.py']);
  expect(lab?.stages[0]?.problems).toEqual([]);
  expect(lab?.stages[0]?.checks).toEqual({});
});

test("a Catch stage has the assistant's tests, its hidden checks and its problems", async () => {
  const { course } = await loadCourse(fixtures, 'demo');
  const check = course?.levels[0]?.modules[0]?.labs[0]?.stages[2];
  expect(check?.kind).toBe('catch');
  expect(Object.keys(check?.tests ?? {})).toEqual(['test_report.py']);
  expect(Object.keys(check?.checks ?? {})).toEqual(['test_report.py']);
  expect(check?.problems.map(({ check, title }) => [check, title])).toEqual([
    ['tst_demo06', 'The fewest votes came first'],
    ['tst_demo07', "It reordered the poll's own list"],
  ]);
  expect(check?.problems[1]?.edit).toEqual({ replace: '    choices.sort()\n', with: '' });
  expect(check?.explanation).toMatch(/^The assistant's tests checked/);
  expect(check?.afterProblems).toMatch(/^`sorted` returns a new list/);
});

test('a Ship stage has hidden tests, its checks and what each requires, and no hints', async () => {
  const { course } = await loadCourse(fixtures, 'demo');
  const ship = course?.levels[0]?.modules[0]?.labs[0]?.stages[3];
  expect(ship?.kind).toBe('ship');
  expect(Object.keys(ship?.tests ?? {})).toEqual(['test_leader.py']);
  expect(Object.keys(ship?.checks ?? {})).toEqual(['test_leader.py']);
  expect(ship?.shipChecks.map(({ check, title }) => [check, title])).toEqual([
    ['tst_demo11', 'Fast on {% $fig.many %} votes'],
    ['tst_demo12', 'Leaves the votes as they were'],
  ]);
  expect(ship?.shipChecks[0]?.failure).toBe('The limit is a second.');
  expect(ship?.hints).toEqual([]);
  expect(ship?.problems).toEqual([]);
});

test('a stage with a chart has what stage.yaml says of it, and chart.py', async () => {
  const { course } = await loadCourse(fixtures, 'demo');
  const [count, share] = course?.levels[0]?.modules[0]?.labs[0]?.stages ?? [];
  expect(count?.chart).toBeNull();
  expect(share?.chart?.title).toBe('The share of yes votes');
  expect(share?.chart?.sliders).toEqual([
    { name: 'votes', label: 'Votes counted', min: 1, max: 3, step: 1, value: 3 },
  ]);
  expect(share?.chart?.code).toMatch(/^import csv\n/);
});

test('a Catch stage being drafted loads with no problems yet, and each check still needs one', async () => {
  const { course, problems } = await loadChanged(async (root) => {
    const path = join(root, stages, 'check/stage.yaml');
    const text = await readFile(path, 'utf8');
    await writeFile(path, `${text.slice(0, text.indexOf('problems:'))}problems: []\n`);
  });
  const lab = course?.levels[0]?.modules[0]?.labs[0];
  expect(lab?.stages.find((stage) => stage.slug === 'check')?.problems).toEqual([]);
  expect(problems).toEqual(
    ['tst_demo06', 'tst_demo07'].map((id) => ({
      path: `${stages}/check/checks/test_report.py`,
      message: `No problem in stage.yaml names the check ${id}.`,
    })),
  );
});

test("a stage's review cards come from cards.yaml, and a stage without one has none", async () => {
  const { course } = await loadCourse(fixtures, 'demo');
  const [count, share, check] = course?.levels[0]?.modules[0]?.labs[0]?.stages ?? [];
  expect(count?.cards.map((card) => card.id)).toEqual(['crd_demo01', 'crd_demo02']);
  expect(count?.cards[0]?.front).toBe("How many of the poll's {% $fig.total %} votes are yes?");
  expect(share?.cards).toEqual([
    {
      id: 'crd_demo03',
      front: "What is a choice's share of the votes?",
      back: 'Its count divided by the total.',
    },
  ]);
  expect(check?.cards).toEqual([]);
});

test("a stage's version stays the same when only its cards change", async () => {
  const before = (await loadCourse(fixtures, 'demo')).course?.levels[0]?.modules[0]?.labs[0];
  const { course } = await loadChanged((root) =>
    edit(join(root, stages, 'share/cards.yaml'), 'divided by', 'over'),
  );
  const after = course?.levels[0]?.modules[0]?.labs[0];
  expect(after?.stages[1]?.cards[0]?.back).toBe('Its count over the total.');
  expect(after?.stages[1]?.version).toBe(before?.stages[1]?.version);
});

test("a Catch stage's version changes when a check does", async () => {
  const before = (await loadCourse(fixtures, 'demo')).course?.levels[0]?.modules[0]?.labs[0];
  const { course } = await loadChanged((root) =>
    edit(join(root, stages, 'check/checks/test_report.py'), '["yes", "no"]', '["no", "yes"]'),
  );
  const after = course?.levels[0]?.modules[0]?.labs[0];
  expect(after?.stages[2]?.version).not.toBe(before?.stages[2]?.version);
});

test("a stage's version changes when any of its files does", async () => {
  const before = (await loadCourse(fixtures, 'demo')).course?.levels[0]?.modules[0]?.labs[0];
  const { course } = await loadChanged((root) =>
    edit(join(root, stages, 'share/hints.md'), 'Divide', 'Split'),
  );
  const after = course?.levels[0]?.modules[0]?.labs[0];
  expect(after?.stages[0]?.version).toBe(before?.stages[0]?.version);
  expect(after?.stages[1]?.version).not.toBe(before?.stages[1]?.version);
});

test("a stage's version changes when its chart.py does", async () => {
  const before = (await loadCourse(fixtures, 'demo')).course?.levels[0]?.modules[0]?.labs[0];
  const { course } = await loadChanged((root) =>
    edit(join(root, stages, 'share/chart.py'), '"share"', '"part"'),
  );
  const after = course?.levels[0]?.modules[0]?.labs[0];
  expect(after?.stages[1]?.version).not.toBe(before?.stages[1]?.version);
});

test('hidden files and folders, such as a tool cache, are not part of a course', async () => {
  let root = '';
  const { problems } = await loadChanged(async (copy) => {
    root = copy;
    await mkdir(join(copy, '.ruff_cache/0.16.10'), { recursive: true });
    await mkdir(join(copy, stages, 'count/.pytest_cache'));
    await writeFile(join(copy, stages, '.DS_Store'), '');
  });
  expect(problems).toEqual([]);
  expect(await courseSlugs(root)).toEqual(['demo']);
});

test.each([
  {
    name: 'a listed stage that is missing',
    change: (root: string) => rm(join(root, stages, 'share'), { recursive: true }),
    problem: { path: `${stages}/share`, message: 'Listed in lab.yaml but missing.' },
  },
  {
    name: 'a stage folder that is not listed',
    change: (root: string) =>
      cp(join(root, stages, 'share'), join(root, stages, 'extra'), { recursive: true }),
    problem: { path: `${stages}/extra`, message: 'Not listed in lab.yaml.' },
  },
  {
    name: 'a file a stage does not use',
    change: (root: string) => writeFile(join(root, stages, 'count/notes.md'), 'Draft\n'),
    problem: {
      path: `${stages}/count/notes.md`,
      message: 'Not part of the course: list it or remove it.',
    },
  },
  {
    name: 'an id of the wrong kind',
    change: (root: string) =>
      edit(join(root, stages, 'count/stage.yaml'), 'stg_demo01', 'lab_demo09'),
    problem: {
      path: `${stages}/count/stage.yaml`,
      message: 'id: Expected a stage id such as ^stg_[0-9a-z]{6}$',
    },
  },
  {
    name: 'a stage that does not say what it builds on',
    change: (root: string) =>
      edit(join(root, stages, 'count/stage.yaml'), 'builds: A new `tally.py`.\n', ''),
    problem: {
      path: `${stages}/count/stage.yaml`,
      message: 'builds: Invalid input: expected string, received undefined',
    },
  },
  {
    name: 'a field the schema does not know',
    change: (root: string) =>
      edit(join(root, stages, 'count/stage.yaml'), 'minutes: 10', 'minutes: 10\nlevel: 2'),
    problem: { path: `${stages}/count/stage.yaml`, message: 'Unrecognized key: "level"' },
  },
  {
    name: 'a tag in prose',
    change: (root: string) =>
      edit(join(root, stages, 'count/brief.md'), 'Write', '{% video /%} Write'),
    problem: { path: `${stages}/count/brief.md`, message: "Undefined tag: 'video'" },
  },
  {
    name: 'an empty hint',
    change: (root: string) =>
      edit(join(root, stages, 'count/hints.md'), '\n---\n', '\n---\n\n---\n'),
    problem: {
      path: `${stages}/count/hints.md`,
      message: 'Each hint, between lines of ---, needs text.',
    },
  },
  {
    name: 'a stage without an explanation',
    change: (root: string) => rm(join(root, stages, 'count/explanation.md')),
    problem: { path: `${stages}/count/explanation.md`, message: 'Missing.' },
  },
  {
    name: 'a line of --- outside a Catch stage',
    change: (root: string) =>
      writeFile(join(root, stages, 'count/explanation.md'), 'Before.\n\n---\n\nAfter.\n'),
    problem: {
      path: `${stages}/count/explanation.md`,
      message: "Only a Catch stage's explanation has a line of ---, where its problems go.",
    },
  },
  {
    name: 'two lines of --- in an explanation',
    change: (root: string) =>
      writeFile(
        join(root, stages, 'check/explanation.md'),
        'One.\n\n---\n\nTwo.\n\n---\n\nThree.\n',
      ),
    problem: {
      path: `${stages}/check/explanation.md`,
      message: 'An explanation has at most one line of ---, where the problems go.',
    },
  },
  {
    name: 'an explanation with nothing after its line of ---',
    change: (root: string) =>
      writeFile(join(root, stages, 'check/explanation.md'), 'Before.\n\n---\n'),
    problem: {
      path: `${stages}/check/explanation.md`,
      message: 'The explanation needs text before and after its line of ---.',
    },
  },
  {
    name: 'Windows line endings',
    change: (root: string) => writeFile(join(root, stages, 'count/brief.md'), 'Write `count`.\r\n'),
    problem: { path: `${stages}/count/brief.md`, message: 'Use LF line endings.' },
  },
  {
    name: 'a test file named the wrong way',
    change: (root: string) => writeFile(join(root, stages, 'count/tests/checks.py'), ''),
    problem: {
      path: `${stages}/count/tests/checks.py`,
      message: 'A test file is named test_<name>.py.',
    },
  },
  {
    name: 'a starter for a different file',
    change: (root: string) => writeFile(join(root, stages, 'count/starter/other.py'), ''),
    problem: {
      path: `${stages}/count/starter/other.py`,
      message: 'Not part of the course: list it or remove it.',
    },
  },
  {
    name: 'hidden checks in a Build stage',
    change: (root: string) =>
      cp(join(root, stages, 'check/checks'), join(root, stages, 'count/checks'), {
        recursive: true,
      }),
    problem: {
      path: `${stages}/count/checks`,
      message: 'Not part of the course: list it or remove it.',
    },
  },
  {
    name: 'a Catch stage without checks',
    change: (root: string) => rm(join(root, stages, 'check/checks'), { recursive: true }),
    problem: { path: `${stages}/check/checks`, message: 'Missing.' },
  },
  {
    name: 'an edit whose text is not in the starter',
    change: (root: string) =>
      edit(join(root, stages, 'check/stage.yaml'), 'replace: "sorted(', 'replace: "sorts('),
    problem: {
      path: `${stages}/check/stage.yaml`,
      message:
        'problems.0.edit: The text to replace must appear once in the starter, but appears 0 times.',
    },
  },
  {
    name: "a problem's check that no check file has",
    change: (root: string) =>
      edit(join(root, stages, 'check/stage.yaml'), 'check: tst_demo06', 'check: tst_demo09'),
    problem: {
      path: `${stages}/check/stage.yaml`,
      message: 'problems.0.check: No check in checks/ has the id tst_demo09.',
    },
  },
  {
    name: 'a check that no problem names',
    change: (root: string) =>
      edit(join(root, stages, 'check/stage.yaml'), 'check: tst_demo06', 'check: tst_demo09'),
    problem: {
      path: `${stages}/check/checks/test_report.py`,
      message: 'No problem in stage.yaml names the check tst_demo06.',
    },
  },
  {
    name: "a tag in a problem's prose",
    change: (root: string) =>
      edit(
        join(root, stages, 'check/stage.yaml'),
        'Leave `choices`',
        '{% video /%} Leave `choices`',
      ),
    problem: {
      path: `${stages}/check/stage.yaml`,
      message: "problems.1.fix: Undefined tag: 'video'",
    },
  },
  {
    name: 'a Ship stage without checks',
    change: (root: string) => rm(join(root, stages, 'ship/checks'), { recursive: true }),
    problem: { path: `${stages}/ship/checks`, message: 'Missing.' },
  },
  {
    name: 'a Ship check that no check file has',
    change: (root: string) =>
      edit(join(root, stages, 'ship/stage.yaml'), 'check: tst_demo12', 'check: tst_demo09'),
    problem: {
      path: `${stages}/ship/stage.yaml`,
      message: 'checks.1.check: No check in checks/ has the id tst_demo09.',
    },
  },
  {
    name: "a check the Ship stage doesn't list",
    change: (root: string) =>
      edit(join(root, stages, 'ship/stage.yaml'), 'check: tst_demo12', 'check: tst_demo09'),
    problem: {
      path: `${stages}/ship/checks/test_leader.py`,
      message: "stage.yaml's checks don't list tst_demo12.",
    },
  },
  {
    name: 'a Ship check listed twice',
    change: (root: string) =>
      edit(join(root, stages, 'ship/stage.yaml'), 'check: tst_demo12', 'check: tst_demo11'),
    problem: {
      path: `${stages}/ship/stage.yaml`,
      message: 'checks.1.check: tst_demo11 is already listed.',
    },
  },
  {
    name: "a tag in a Ship check's text",
    change: (root: string) =>
      edit(
        join(root, stages, 'ship/stage.yaml'),
        'The limit is a second.',
        '{% video /%} The limit is a second.',
      ),
    problem: {
      path: `${stages}/ship/stage.yaml`,
      message: "checks.0.failure: Undefined tag: 'video'",
    },
  },
  {
    name: 'a Catch stage on a file an earlier stage made',
    change: async (root: string) => {
      await edit(join(root, stages, 'check/stage.yaml'), 'file: report.py', 'file: tally.py');
      for (const folder of ['starter', 'solution']) {
        await cp(
          join(root, stages, `check/${folder}/report.py`),
          join(root, stages, `check/${folder}/tally.py`),
        );
        await rm(join(root, stages, `check/${folder}/report.py`));
      }
    },
    problem: {
      path: `${stages}/check/stage.yaml`,
      message:
        "file: A Catch stage's file is the assistant's, so no earlier stage may make tally.py.",
    },
  },
  {
    name: 'a Problem stage on a file an earlier stage made',
    change: (root: string) =>
      edit(join(root, stages, 'share/stage.yaml'), 'kind: build', 'kind: problem'),
    problem: {
      path: `${stages}/share/stage.yaml`,
      message:
        'file: A Problem stage starts from a file of its own, so no earlier stage may make tally.py.',
    },
  },
  {
    name: 'a chart without chart.py',
    change: (root: string) => rm(join(root, stages, 'share/chart.py')),
    problem: {
      path: `${stages}/share/chart.py`,
      message: 'Missing: stage.yaml has a chart, which chart.py draws.',
    },
  },
  {
    name: 'a chart.py that stage.yaml has no chart for',
    change: (root: string) =>
      cp(join(root, stages, 'share/chart.py'), join(root, stages, 'count/chart.py')),
    problem: {
      path: `${stages}/count/chart.py`,
      message: 'stage.yaml has no chart for it to draw.',
    },
  },
  {
    name: 'a card with an id of the wrong kind',
    change: (root: string) =>
      edit(join(root, stages, 'share/cards.yaml'), 'crd_demo03', 'stg_demo03'),
    problem: {
      path: `${stages}/share/cards.yaml`,
      message: 'cards.0.id: Expected a card id such as ^crd_[0-9a-z]{6}$',
    },
  },
  {
    name: 'a card without an answer',
    change: (root: string) =>
      edit(
        join(root, stages, 'share/cards.yaml'),
        '    back: Its count divided by the total.\n',
        '',
      ),
    problem: {
      path: `${stages}/share/cards.yaml`,
      message: 'cards.0.back: Invalid input: expected string, received undefined',
    },
  },
  {
    name: 'a cards.yaml with no cards',
    change: (root: string) => writeFile(join(root, stages, 'share/cards.yaml'), 'cards: []\n'),
    problem: {
      path: `${stages}/share/cards.yaml`,
      message: 'cards: Too small: expected array to have >=1 items',
    },
  },
  {
    name: 'a tag in a card',
    change: (root: string) =>
      edit(join(root, stages, 'share/cards.yaml'), 'divided by', 'divided {% video /%} by'),
    problem: {
      path: `${stages}/share/cards.yaml`,
      message: "cards.0.back: Undefined tag: 'video'",
    },
  },
  {
    name: 'a slider that starts off its steps',
    change: (root: string) =>
      edit(join(root, stages, 'share/stage.yaml'), 'value: 3', 'value: 2.5'),
    problem: {
      path: `${stages}/share/stage.yaml`,
      message: 'chart.sliders.0.value: value must be in the range, on a step.',
    },
  },
  {
    name: 'a slider without the end of its range',
    change: (root: string) => edit(join(root, stages, 'share/stage.yaml'), '      max: 3\n', ''),
    problem: {
      path: `${stages}/share/stage.yaml`,
      message: 'chart.sliders.0.max: Invalid input: expected number, received undefined',
    },
  },
  {
    name: 'stops that go down',
    change: (root: string) =>
      edit(
        join(root, stages, 'share/stage.yaml'),
        '      min: 1\n      max: 3\n      step: 1\n',
        '      stops: [1, 3, 2]\n',
      ),
    problem: {
      path: `${stages}/share/stage.yaml`,
      message: 'chart.sliders.0.stops: Each stop must be more than the one before.',
    },
  },
  {
    name: "a learner's file named chart.py in a lab with a chart",
    change: async (root: string) => {
      await edit(join(root, stages, 'ship/stage.yaml'), 'file: report.py', 'file: chart.py');
      for (const folder of ['starter', 'solution']) {
        await cp(
          join(root, stages, `ship/${folder}/report.py`),
          join(root, stages, `ship/${folder}/chart.py`),
        );
        await rm(join(root, stages, `ship/${folder}/report.py`));
      }
    },
    problem: {
      path: `${stages}/ship/stage.yaml`,
      message:
        "file: chart.py is the name a stage's chart runs as, so the learner's file needs another.",
    },
  },
  {
    name: 'a reference that is not JSON',
    change: (root: string) => writeFile(join(root, references, 'shares.json'), '{"polls": [\n'),
    problem: {
      path: `${references}/shares.json`,
      message: expect.stringMatching(/^Not valid JSON: /),
    },
  },
  {
    name: 'references without the make.py that records them',
    change: (root: string) => rm(join(root, references, 'make.py')),
    problem: { path: `${references}/make.py`, message: 'Missing.' },
  },
  {
    name: "a reference lab.yaml doesn't list",
    change: (root: string) => writeFile(join(root, references, 'votes.json'), '[]\n'),
    problem: {
      path: `${references}/votes.json`,
      message: 'Not part of the course: list it or remove it.',
    },
  },
  {
    name: 'a project without its lock',
    change: (root: string) => rm(join(root, project, 'uv.lock')),
    problem: { path: `${project}/uv.lock`, message: 'Missing.' },
  },
  {
    name: 'a file a project does not use',
    change: (root: string) => writeFile(join(root, project, 'notes.md'), 'Draft\n'),
    problem: {
      path: `${project}/notes.md`,
      message: 'Not part of the course: list it or remove it.',
    },
  },
  {
    name: "a learner's file named as a project's file",
    change: async (root: string) => {
      await edit(join(root, stages, 'ship/stage.yaml'), 'file: report.py', 'file: conftest.py');
      for (const folder of ['starter', 'solution']) {
        await cp(
          join(root, stages, `ship/${folder}/report.py`),
          join(root, stages, `ship/${folder}/conftest.py`),
        );
        await rm(join(root, stages, `ship/${folder}/report.py`));
      }
      await writeFile(join(root, project, 'conftest.py'), 'import pytest\n');
    },
    problem: {
      path: `${stages}/ship/stage.yaml`,
      message:
        "file: conftest.py is a file of the lab's project, so the learner's file needs another name.",
    },
  },
])('$name is a problem', async ({ change, problem }) => {
  const { problems } = await loadChanged(change);
  expect(problems).toContainEqual(problem);
});

const ledger = 'demo/modules/ledgers/labs/ledger';

test("a lab that runs on the learner's machine says so, and has its project", async () => {
  const { course, problems } = await loadCourse(fixtures, 'demo');
  expect(problems).toEqual([]);
  expect(course?.levels[0]?.modules[0]?.labs[0]?.runs).toBe('browser');
  const lab = course?.levels[1]?.modules[0]?.labs[0];
  expect(lab?.runs).toBe('machine');
  expect(lab?.stages.map(({ slug, kind }) => [slug, kind])).toEqual([
    ['balance', 'build'],
    ['audit', 'catch'],
    ['close', 'ship'],
  ]);
  expect(Object.keys(lab?.project ?? {})).toEqual(['README.md', 'pyproject.toml', 'uv.lock']);
});

test('a machine lab lists the files it fetches, with their credit', async () => {
  const { course } = await loadCourse(fixtures, 'demo');
  const lab = course?.levels[1]?.modules[0]?.labs[0];
  expect(lab?.fetch.map(({ kind, title, licence }) => [kind, title, licence.name])).toEqual([
    ['data', 'Fashion-MNIST', 'MIT'],
  ]);
  expect(lab?.fetch[0]?.files).toEqual([
    {
      file: 't10k-labels-idx1-ubyte.gz',
      url: 'https://fashion-mnist.s3.eu-central-1.amazonaws.com/t10k-labels-idx1-ubyte.gz',
      bytes: 5148,
      sha256: '67da17c76eaffca5446c3361aaab5c3cd6d1c2608764d35dfb1850b086bf8dd5',
    },
  ]);
});

test('a machine lab names the models it serves, each with its kind and credit', async () => {
  const { course } = await loadCourse(fixtures, 'demo');
  const lab = course?.levels[1]?.modules[0]?.labs[0];
  expect(lab?.models.map(({ title, kind, licence }) => [title, kind, licence.name])).toEqual([
    ['stories260K', 'chat', 'MIT'],
    ['bge-small-en-v1.5', 'embedding', 'MIT'],
    ['jina-reranker-v1-tiny-en', 'reranking', 'Apache License 2.0'],
  ]);
  expect(lab?.models[0]?.file).toEqual({
    url: 'https://huggingface.co/ggml-org/test-model-stories260K/resolve/479896ec924af6d40fd419ab8f4d1eb2101de00d/stories260K-f32.gguf',
    bytes: 1185376,
    sha256: '270cba1bd5109f42d03350f60406024560464db173c0e387d91f0426d3bd256d',
  });
});

test("a lab's model is a .gguf file, pinned by its address, size and sha256", async () => {
  const { problems } = await loadChanged(async (root) => {
    const yaml = join(root, ledger, 'lab.yaml');
    await edit(yaml, 'stories260K-f32.gguf', 'stories260K-f32.bin');
    await edit(yaml, 'bytes: 1185376', 'bytes: -1');
    await edit(yaml, 'sha256: 270c', 'sha256: 270C');
  });
  const fields = problems
    .filter(({ path }) => path === `${ledger}/lab.yaml`)
    .map(({ message }) => message.split(':')[0]);
  expect(fields).toEqual(['models.0.file.url', 'models.0.file.bytes', 'models.0.file.sha256']);
});

test("a lab's models each have a kind and a title of their own, which a request can give", async () => {
  const { problems } = await loadChanged(async (root) => {
    const yaml = join(root, ledger, 'lab.yaml');
    await edit(yaml, 'kind: reranking', 'kind: vision');
    await edit(yaml, 'title: jina-reranker-v1-tiny-en', 'title: bge-small-en-v1.5');
    await edit(yaml, 'title: stories260K', 'title: stories 260K');
  });
  expect(
    problems.filter(({ path }) => path === `${ledger}/lab.yaml`).map(({ message }) => message),
  ).toEqual([
    'models.0.title: Expected letters, digits, dots, dashes and _',
    'models.2.kind: Invalid option: expected one of "chat"|"embedding"|"reranking"',
  ]);
  const { problems: shared } = await loadChanged(async (root) => {
    const yaml = join(root, ledger, 'lab.yaml');
    await edit(yaml, 'title: jina-reranker-v1-tiny-en', 'title: bge-small-en-v1.5');
  });
  expect(shared.filter(({ path }) => path === `${ledger}/lab.yaml`)).toEqual([
    { path: `${ledger}/lab.yaml`, message: 'models: Each model needs a title of its own.' },
  ]);
});

test('a lab that runs in the browser serves no models', async () => {
  const { problems } = await loadChanged(async (root) => {
    const model = (await readFile(join(root, ledger, 'lab.yaml'), 'utf8')).match(
      /^models:\n(?: {2}.*\n)+/m,
    )?.[0];
    if (!model) throw new Error("The ledger lab's lab.yaml has no models.");
    await edit(
      join(root, 'demo/modules/counting/labs/tallies/lab.yaml'),
      'stages:',
      `${model}stages:`,
    );
  });
  expect(problems).toEqual([
    {
      path: 'demo/modules/counting/labs/tallies/lab.yaml',
      message:
        "models: Only a lab that runs on the learner's machine serves models there: set runs: machine.",
    },
  ]);
});

test('a file a lab fetches is pinned by its address, size and sha256', async () => {
  const { problems } = await loadChanged(async (root) => {
    const yaml = join(root, ledger, 'lab.yaml');
    await edit(yaml, 'file: t10k-labels-idx1-ubyte.gz', 'file: labels.gz.partial');
    await edit(yaml, 'url: https://fashion-mnist.s3', 'url: http://fashion-mnist.s3');
    await edit(yaml, 'bytes: 5148', 'bytes: 0');
    await edit(yaml, 'sha256: 67da', 'sha256: 67DA');
  });
  // A lab.yaml that breaks its schema leaves the lab's folders unlisted, which are problems too.
  const fields = problems
    .filter(({ path }) => path === `${ledger}/lab.yaml`)
    .map(({ message }) => message.split(':')[0]);
  expect(fields).toEqual([
    'fetch.0.files.0.file',
    'fetch.0.files.0.url',
    'fetch.0.files.0.bytes',
    'fetch.0.files.0.sha256',
  ]);
});

test('each file a lab fetches has a name of its own in data/', async () => {
  const { problems } = await loadChanged((root) =>
    edit(join(root, ledger, 'lab.yaml'), 'file: t10k-labels-idx1-ubyte.gz', 'file: Entries.csv'),
  );
  expect(problems).toEqual([
    {
      path: `${ledger}/lab.yaml`,
      message: 'fetch.0.files.0.file: data/ already has a file named Entries.csv.',
    },
  ]);
});

test('a lab that runs in the browser fetches no files', async () => {
  const { problems } = await loadChanged(async (root) => {
    const fetched = (await readFile(join(root, ledger, 'lab.yaml'), 'utf8')).match(
      /^fetch:\n(?: {2}.*\n)+/m,
    )?.[0];
    if (!fetched) throw new Error("The ledger lab's lab.yaml has no fetch.");
    await edit(
      join(root, 'demo/modules/counting/labs/tallies/lab.yaml'),
      'stages:',
      `${fetched}stages:`,
    );
  });
  expect(problems).toEqual([
    {
      path: 'demo/modules/counting/labs/tallies/lab.yaml',
      message:
        "fetch: Only a lab that runs on the learner's machine fetches files: set runs: machine, or serve the data as a dataset.",
    },
  ]);
});

test("a lab that runs on the learner's machine runs from its project", async () => {
  const { problems } = await loadChanged((root) =>
    rm(join(root, ledger, 'project'), { recursive: true }),
  );
  expect(problems).toEqual([
    {
      path: `${ledger}/project`,
      message: "Missing: a lab that runs on the learner's machine runs from its project.",
    },
  ]);
});

test("a machine lab's stages have no chart, no Problem stage and no file named sulba.py", async () => {
  const { problems } = await loadChanged(async (root) => {
    const balance = join(root, ledger, 'stages/balance');
    await edit(
      join(balance, 'stage.yaml'),
      'minutes: 10\n',
      'minutes: 10\nchart:\n  title: Balance\n',
    );
    await writeFile(join(balance, 'chart.py'), 'def chart():\n    pass\n');
    const close = join(root, ledger, 'stages/close');
    const yaml = await readFile(join(close, 'stage.yaml'), 'utf8');
    await writeFile(
      join(close, 'stage.yaml'),
      yaml.replace('kind: ship', 'kind: problem').split('checks:')[0] ?? '',
    );
    await rm(join(close, 'checks'), { recursive: true });
    const audit = join(root, ledger, 'stages/audit');
    await edit(join(audit, 'stage.yaml'), 'file: audit.py', 'file: sulba.py');
    for (const folder of ['starter', 'solution']) {
      await cp(join(audit, folder, 'audit.py'), join(audit, folder, 'sulba.py'));
      await rm(join(audit, folder, 'audit.py'));
    }
  });
  expect(problems).toEqual([
    {
      path: `${ledger}/stages/balance/stage.yaml`,
      message:
        "chart: A chart is drawn in the browser, so a lab that runs on the learner's machine can't have one.",
    },
    {
      path: `${ledger}/stages/audit/stage.yaml`,
      message:
        "file: sulba.py is the runner a machine lab's download carries, so the learner's file needs another name.",
    },
    {
      path: `${ledger}/stages/close/stage.yaml`,
      message:
        "kind: A Problem stage's clock runs in the browser, so a lab that runs on the learner's machine can't have one.",
    },
  ]);
});

test("a lab that runs in the browser can't load a package Pyodide doesn't ship", async () => {
  const { problems } = await loadChanged((root) =>
    edit(
      join(root, stages, 'count/stage.yaml'),
      'minutes: 10\n',
      'minutes: 10\npackages: [torch]\n',
    ),
  );
  expect(problems).toEqual([
    {
      path: `${stages}/count/stage.yaml`,
      message:
        "packages: Pyodide has no torch, so a lab whose stages load it runs on the learner's machine: set runs: machine in lab.yaml.",
    },
  ]);
});

import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { afterEach, expect, test } from 'vitest';
import { courseSlugs, loadCourse } from './load.ts';

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const stages = 'demo/modules/counting/labs/tallies/stages';
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
  expect(lab?.code.map(({ title, licence }) => [title, licence.name])).toEqual([
    ['tally.js 1.0.0', 'MIT'],
  ]);
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
])('$name is a problem', async ({ change, problem }) => {
  const { problems } = await loadChanged(change);
  expect(problems).toContainEqual(problem);
});

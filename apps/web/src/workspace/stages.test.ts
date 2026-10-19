import { expect, test } from 'vitest';
import type { LabView, StageView } from '../lib/labs';
import {
  chartOf,
  codeOf,
  downloadOf,
  isOpen,
  type Kept,
  machineDownloadOf,
  packagesOf,
  previewOf,
  type Review,
  runOf,
} from './stages';

function stage(
  id: string,
  file: string,
  starter: string,
  packages: StageView['packages'] = [],
): StageView {
  return {
    id,
    slug: id,
    kind: 'build',
    title: id,
    file,
    packages,
    minutes: 10,
    version: id,
    brief: '',
    builds: '',
    hints: [],
    explanation: '',
    afterProblems: null,
    starter,
    solution: `${starter}# solved\n`,
    tests: { [`tests/test_${id}.py`]: `# tests for ${id}\n` },
    checks: {},
    problems: [],
    shipChecks: [],
    chart: null,
  };
}

/** A Catch stage: the assistant's draft of screener.py, with two problems. */
const review: StageView = {
  ...stage('three', 'screener.py', 'class Screener:\n    draft = True\n', ['scikit-learn']),
  kind: 'catch',
  checks: { 'tests/checks/test_three.py': '# checks for three\n' },
  problems: [
    { check: 'tst_three1', title: 'One', cost: '', fix: '' },
    { check: 'tst_three2', title: 'Two', cost: '', fix: '' },
  ],
};

/** The lab's data, as the workspace fetches it. */
const data = { 'data/votes.csv': 'choice\nyes\n' };

const lab: LabView = {
  id: 'lab_test01',
  path: 'course/module/lab',
  runs: 'browser',
  title: 'Lab',
  summary: 'A lab.',
  course: 'Course',
  level: 'Level',
  module: 'Module',
  data: [],
  references: [],
  fetch: [],
  model: null,
  project: [],
  stages: [
    stage('one', 'model.py', 'def a():\n    pass\n', ['numpy']),
    stage('two', 'model.py', 'def b():\n    pass\n'),
    review,
    stage('four', 'screener.py', 'def threshold():\n    pass\n'),
  ],
};

function keeping(
  code: Record<string, string>,
  passed: string[] = [],
  reviews: Record<string, Review> = {},
): Kept {
  return {
    code: (id) => code[id] ?? null,
    passed: (id) => passed.includes(id),
    review: (id) => reviews[id] ?? null,
  };
}

test('a stage the learner has worked on opens with their code', () => {
  expect(codeOf(lab, 1, keeping({ two: 'mine\n' }))).toBe('mine\n');
});

test('the first stage on a file opens with its starter', () => {
  expect(codeOf(lab, 0, keeping({}))).toBe('def a():\n    pass\n');
  expect(codeOf(lab, 2, keeping({ one: 'mine\n' }))).toBe('class Screener:\n    draft = True\n');
});

test("a later stage on a file opens with its starter below the learner's code", () => {
  expect(codeOf(lab, 1, keeping({ one: 'def a():\n    return 1\n' }))).toBe(
    'def a():\n    return 1\n\n\ndef b():\n    pass\n',
  );
});

test('a stage passed on another device carries on its solution in this browser', () => {
  expect(codeOf(lab, 1, keeping({}, ['one']))).toBe(
    'def a():\n    pass\n# solved\n\n\ndef b():\n    pass\n',
  );
  expect(
    runOf(lab, data, 2, 'x = 1\n', keeping({ one: 'A\n' }, ['one', 'two'])).files['model.py'],
  ).toBe(lab.stages[1]?.solution);
});

test("a Catch run has the lab's data, the learner's code, the assistant's tests and the checks", () => {
  const run = runOf(
    lab,
    data,
    2,
    'class Screener:\n    ok = True\n',
    keeping({ one: 'A\n', two: 'B\n' }),
  );
  expect(run).toEqual({
    files: {
      'data/votes.csv': 'choice\nyes\n',
      'model.py': 'B\n',
      'screener.py': 'class Screener:\n    ok = True\n',
      'tests/test_three.py': '# tests for three\n',
      'tests/checks/test_three.py': '# checks for three\n',
    },
    tests: ['tests/test_three.py', 'tests/checks/test_three.py'],
    packages: ['numpy', 'scikit-learn'],
  });
});

test('after a review that missed a problem, the next stage on the file builds on the fixed code', () => {
  const kept = keeping({ three: 'mine\n' }, ['one', 'two', 'three'], {
    three: { caught: ['tst_three1'], total: 2 },
  });
  expect(codeOf(lab, 3, kept)).toBe(
    'class Screener:\n    draft = True\n# solved\n\n\ndef threshold():\n    pass\n',
  );
});

test("after a review that caught every problem, the next stage builds on the learner's code", () => {
  const kept = keeping({ three: 'mine\n' }, ['one', 'two', 'three'], {
    three: { caught: ['tst_three1', 'tst_three2'], total: 2 },
  });
  expect(codeOf(lab, 3, kept)).toBe('mine\n\n\ndef threshold():\n    pass\n');
});

test("a later stage's runs use the code the Catch stage carried on", () => {
  const later: LabView = {
    ...lab,
    stages: [...lab.stages.slice(0, 3), stage('four', 'report.py', 'def report():\n    pass\n')],
  };
  const passed = ['one', 'two', 'three'];
  const missed = keeping({ three: 'mine\n' }, passed, {
    three: { caught: ['tst_three1'], total: 2 },
  });
  const caught = keeping({ three: 'mine\n' }, passed, {
    three: { caught: ['tst_three1', 'tst_three2'], total: 2 },
  });
  expect(runOf(later, data, 3, 'x = 1\n', missed).files['screener.py']).toBe(review.solution);
  expect(runOf(later, data, 3, 'x = 1\n', caught).files['screener.py']).toBe('mine\n');
});

test("a download has the project's files, the lab's data and the learner's files, but no tests", () => {
  const project = { 'pyproject.toml': '[project]\n', 'README.md': '# Lab\n' };
  const files = downloadOf(
    lab,
    data,
    3,
    'def threshold():\n    return 0.5\n',
    keeping({ one: 'A\n', two: 'B\n', three: 'C\n' }, ['one', 'two', 'three'], {
      three: { caught: ['tst_three1', 'tst_three2'], total: 2 },
    }),
    project,
  );
  expect(files).toEqual({
    'pyproject.toml': '[project]\n',
    'README.md': '# Lab\n',
    'data/votes.csv': 'choice\nyes\n',
    'model.py': 'B\n',
    'screener.py': 'def threshold():\n    return 0.5\n',
  });
});

test("a download leaves out the lab's references, as it leaves out its tests", () => {
  const recorded: LabView = {
    ...lab,
    references: [
      { path: 'references/shares.json', served: '/references/0123456789abcdef/shares.json' },
    ],
  };
  const fetched = { ...data, 'references/shares.json': '{"polls": []}\n' };
  const kept = keeping({}, [], {});
  expect(runOf(recorded, fetched, 0, 'A\n', kept).files['references/shares.json']).toBe(
    '{"polls": []}\n',
  );
  expect(downloadOf(recorded, fetched, 0, 'A\n', kept, {})).toEqual({
    'data/votes.csv': 'choice\nyes\n',
    'model.py': 'A\n',
  });
});

test("a chart draws with the learner's files, as a run has them, and chart.py", () => {
  const chart = { title: 'Chart', sliders: [], code: '# draws\n' };
  const charted: LabView = {
    ...lab,
    stages: lab.stages.map((each, at) => (at === 1 ? { ...each, chart } : each)),
  };
  expect(chartOf(charted, data, 1, 'mine\n', keeping({ one: 'A\n' }), { w: 1 })).toEqual({
    files: { 'data/votes.csv': 'choice\nyes\n', 'model.py': 'mine\n', 'chart.py': '# draws\n' },
    values: { w: 1 },
    packages: ['numpy'],
  });
});

test("a chart's preview draws with every stage's solution up to it", () => {
  const chart = { title: 'Chart', sliders: [], code: '# draws\n' };
  const charted: LabView = {
    ...lab,
    stages: lab.stages.map((each, at) => (at === 2 ? { ...each, chart } : each)),
  };
  expect(previewOf(charted, data, 2, {}).files).toEqual({
    'data/votes.csv': 'choice\nyes\n',
    'model.py': 'def b():\n    pass\n# solved\n',
    'screener.py': 'class Screener:\n    draft = True\n# solved\n',
    'chart.py': '# draws\n',
  });
});

test("a stage loads its own packages and every earlier stage's, never a later stage's", () => {
  expect(packagesOf(lab, 0)).toEqual(['numpy']);
  expect(packagesOf(lab, 1)).toEqual(['numpy']);
  expect(packagesOf(lab, 2)).toEqual(['numpy', 'scikit-learn']);
});

test('a stage opens once the stage before it is passed', () => {
  expect(isOpen(lab, 0, keeping({}))).toBe(true);
  expect(isOpen(lab, 1, keeping({}))).toBe(false);
  expect(isOpen(lab, 1, keeping({}, ['one']))).toBe(true);
  expect(isOpen(lab, 2, keeping({}, ['one']))).toBe(false);
});

test("a machine lab's download opens at the first stage not done, on the solutions before it", () => {
  const machine: LabView = { ...lab, runs: 'machine' };
  const data = { 'data/votes.csv': 'choice\nyes\n', 'references/shares.json': '{}\n' };
  const project = { 'README.md': '# Lab\n', 'sulba.py': '# the runner\n' };
  const page = 'https://sulba.dev/course/module/lab/';
  const files = machineDownloadOf(machine, data, keeping({}, ['one']), project, page, (html) =>
    html.toUpperCase(),
  );
  const { '.sulba/lab.json': labJson, ...others } = files;
  // The learner's code stays on their machine, so stage two goes on from stage one's solution.
  expect(others).toEqual({
    'README.md': '# Lab\n',
    'sulba.py': '# the runner\n',
    'data/votes.csv': 'choice\nyes\n',
    '.sulba/references/shares.json': '{}\n',
    'model.py': 'def a():\n    pass\n# solved\n\n\ndef b():\n    pass\n',
  });
  const written = JSON.parse(labJson ?? '');
  expect(written).toMatchObject({ format: 1, id: 'lab_test01', title: 'Lab', page, start: 1 });
  const [, , three] = written.stages;
  expect(three).toMatchObject({ id: 'three', kind: 'catch', file: 'screener.py' });
  expect(three.checks).toEqual([
    { id: 'tst_three1', title: 'One', requires: '', failure: '' },
    { id: 'tst_three2', title: 'Two', requires: '', failure: '' },
  ]);
  // Its tests and fixed code are there for the runner, in base64.
  expect(atob(three.tests['tests/checks/test_three.py'])).toBe('# checks for three\n');
  expect(atob(three.fixed)).toBe('class Screener:\n    draft = True\n# solved\n');
  expect(written.stages[0].fixed).toBeNull();
});

test("a machine lab's download tells its runner the lab's datasets and the files it fetches", () => {
  const labels = {
    file: 'labels.gz',
    url: 'https://example.com/labels.gz',
    bytes: 5148,
    sha256: '67da17c76eaffca5446c3361aaab5c3cd6d1c2608764d35dfb1850b086bf8dd5',
  };
  const machine: LabView = {
    ...lab,
    runs: 'machine',
    data: [
      {
        file: 'votes.csv',
        title: 'Votes',
        creators: ['Sulba'],
        url: 'https://example.com/votes',
        licence: { name: 'CC0 1.0', url: 'https://example.com/cc0' },
        changes: 'Made up.',
        path: 'data/votes.csv',
        served: '/data/0123456789abcdef/votes.csv',
      },
    ],
    fetch: [
      {
        kind: 'data',
        title: 'Labels',
        creators: ['Sulba'],
        url: 'https://example.com/labels',
        licence: { name: 'MIT', url: 'https://example.com/mit' },
        files: [labels],
      },
    ],
  };
  const files = machineDownloadOf(
    machine,
    data,
    keeping({}),
    {},
    'https://sulba.dev/',
    (html) => html,
  );
  const written = JSON.parse(files['.sulba/lab.json'] ?? '');
  expect(written.data).toEqual(['data/votes.csv']);
  expect(written.fetch).toEqual([labels]);
  // The runner fetches them, so the download doesn't carry them.
  expect(Object.keys(files)).not.toContain('data/labels.gz');
});

test('a machine lab done to its end downloads at its last stage', () => {
  const machine: LabView = { ...lab, runs: 'machine' };
  const done = keeping({}, ['one', 'two', 'three', 'four'], {
    three: { caught: ['tst_three1'], total: 2 },
  });
  const files = machineDownloadOf(machine, {}, done, {}, 'https://sulba.dev/', (html) => html);
  expect(JSON.parse(files['.sulba/lab.json'] ?? '').start).toBe(3);
  // The review missed a problem, so the files go on from the fixed screener.
  expect(files['screener.py']).toBe(
    'class Screener:\n    draft = True\n# solved\n\n\ndef threshold():\n    pass\n',
  );
});

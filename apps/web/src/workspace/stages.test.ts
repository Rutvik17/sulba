import { expect, test } from 'vitest';
import type { LabView, StageView } from '../lib/labs';
import { codeOf, isOpen, type Kept, packagesOf, type Review, runOf } from './stages';

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
    hints: [],
    explanation: '',
    afterProblems: null,
    starter,
    solution: `${starter}# solved\n`,
    tests: { [`tests/test_${id}.py`]: `# tests for ${id}\n` },
    checks: {},
    problems: [],
    shipChecks: [],
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

const lab: LabView = {
  id: 'lab_test01',
  path: 'course/module/lab',
  title: 'Lab',
  summary: 'A lab.',
  course: 'Course',
  level: 'Level',
  module: 'Module',
  data: [],
  files: { 'data/votes.csv': 'choice\nyes\n' },
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

test("a Catch run has the lab's data, the learner's code, the assistant's tests and the checks", () => {
  const run = runOf(
    lab,
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
  expect(runOf(later, 3, 'x = 1\n', missed).files['screener.py']).toBe(review.solution);
  expect(runOf(later, 3, 'x = 1\n', caught).files['screener.py']).toBe('mine\n');
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

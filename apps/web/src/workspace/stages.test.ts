import { expect, test } from 'vitest';
import type { LabView, StageView } from '../lib/labs';
import { codeOf, isOpen, type Kept, packagesOf, runOf } from './stages';

function stage(id: string, file: string, starter: string, packages: StageView['packages'] = []) {
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
    starter,
    solution: `${starter}# solved\n`,
    tests: { [`tests/test_${id}.py`]: `# tests for ${id}\n` },
  } satisfies StageView;
}

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
    stage('three', 'screener.py', 'class Screener:\n    pass\n', ['scikit-learn']),
  ],
};

function keeping(code: Record<string, string>, passed: string[] = []): Kept {
  return { code: (id) => code[id] ?? null, passed: (id) => passed.includes(id) };
}

test('a stage the learner has worked on opens with their code', () => {
  expect(codeOf(lab, 1, keeping({ two: 'mine\n' }))).toBe('mine\n');
});

test('the first stage on a file opens with its starter', () => {
  expect(codeOf(lab, 0, keeping({}))).toBe('def a():\n    pass\n');
  expect(codeOf(lab, 2, keeping({ one: 'mine\n' }))).toBe('class Screener:\n    pass\n');
});

test("a later stage on a file opens with its starter below the learner's code", () => {
  expect(codeOf(lab, 1, keeping({ one: 'def a():\n    return 1\n' }))).toBe(
    'def a():\n    return 1\n\n\ndef b():\n    pass\n',
  );
});

test("a run has the lab's data, the stage's tests, and the learner's code for every file", () => {
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
    },
    tests: ['tests/test_three.py'],
    packages: ['numpy', 'scikit-learn'],
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

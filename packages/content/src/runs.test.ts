import { fileURLToPath } from 'node:url';
import { expect, test } from 'vitest';
import { loadCourse } from './load.ts';
import { addStarter, stageRuns } from './runs.ts';

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const { course } = await loadCourse(fixtures, 'demo');
const lab = course?.levels[0]?.modules[0]?.labs[0];
if (!lab) throw new Error('The fixture course has no lab.');
const [count, share, check] = stageRuns(lab);

test("a stage's starter goes below the learner's code, after two blank lines", () => {
  expect(addStarter('def a():\n    pass\n\n', 'def b():\n    pass\n')).toBe(
    'def a():\n    pass\n\n\ndef b():\n    pass\n',
  );
});

test('the first stage on a file starts from its starter', () => {
  expect(count?.starter.files['tally.py']).toBe(lab.stages[0]?.starter);
  expect(count?.earlier).toBeNull();
});

test("a later stage on the same file starts from the earlier stage's solution", () => {
  expect(share?.starter.files['tally.py']).toBe(
    addStarter(lab.stages[0]?.solution ?? '', lab.stages[1]?.starter ?? ''),
  );
  expect(share?.solution.files['tally.py']).toBe(lab.stages[1]?.solution);
});

test("every run has the lab's data and only its own stage's tests", () => {
  expect(share?.solution.files['data/votes.csv']).toBe('choice\nyes\nno\nyes\n');
  expect(share?.solution.tests).toEqual(['tests/test_tally.py']);
});

test("the earlier stages' tests run against a later solution, a folder each", () => {
  expect(share?.earlier?.tests).toEqual(['tests/count/test_tally.py']);
  expect(share?.earlier?.files['tally.py']).toBe(lab.stages[1]?.solution);
});

test("a Catch stage runs the assistant's tests, then its hidden checks in tests/checks", () => {
  expect(check?.solution.tests).toEqual(['tests/test_report.py', 'tests/checks/test_report.py']);
  expect(check?.starter.files['report.py']).toBe(lab.stages[2]?.starter);
  expect(check?.starter.files['tests/checks/test_report.py']).toBe(
    lab.stages[2]?.checks['test_report.py'],
  );
});

test('each problem gets a run of the starter with only its own edit made', () => {
  const [order, list] = check?.fixes ?? [];
  expect(order?.files['report.py']).toContain('key=lambda each: -share(choices, each)');
  expect(order?.files['report.py']).toContain('choices.sort()');
  expect(list?.files['report.py']).not.toContain('choices.sort()');
  expect(list?.files['report.py']).toContain('for choice in sorted(set(choices))]');
  expect(count?.fixes).toEqual([]);
});

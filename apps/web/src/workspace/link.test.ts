import { deflateSync } from 'fflate';
import { expect, test } from 'vitest';
import type { LabView, StageView } from '../lib/labs';
import { reportOf } from './link';

function stage(id: string, kind: StageView['kind'], problems: string[] = []): StageView {
  return {
    id,
    slug: id,
    kind,
    title: id,
    file: `${id}.py`,
    packages: [],
    minutes: 10,
    version: 'v1',
    brief: '',
    builds: '',
    hints: [],
    explanation: '',
    afterProblems: null,
    starter: '',
    solution: '',
    tests: {},
    checks: {},
    problems: problems.map((check) => ({ check, title: check, cost: '', fix: '' })),
    shipChecks: [],
    chart: null,
  };
}

const lab: LabView = {
  id: 'lab_tally1',
  path: 'demo/counting/tallies',
  runs: 'machine',
  title: 'Tallies',
  summary: '',
  course: 'Demo',
  level: 'First',
  module: 'Counting',
  data: [],
  references: [],
  fetch: [],
  model: null,
  project: [],
  stages: [
    stage('stg_count1', 'build'),
    stage('stg_review', 'catch', ['tst_eeeeee', 'tst_ffffff']),
  ],
};

/** A link from the runner, which its own tests make (packages/lab/python/tests/test_sulba.py). */
const link =
  '#run=jZDPasMwDMbfRWd7WK7zz8-x00IIsmN3AycpidNRSt69dnbpIYcJ8YEk0PeTnuDnZaQIGhkEMqCz9pFCeCAwuNG6ugH0E9Z47e28TRFBT1sI7Ogs7v7jfvPc0nb9TntaiGvs3RHQpQ3LbIIbV9By3xlQjG68xVS2LQhTeemV48VwsVw5JN5QIXllSy-cHGqDGeLNiME9d5ZtAtYiwy6r7NhBpCQDKWTJUXCsP7HUQqT8EEJ8wfsocbVQkLDVIA1vnEKufEm8tpeBS4NO-IYShDo1zz-BP8dD_nc7q8_g6jO4bn8B';

/** A link carrying `payload`, written as the runner writes one. */
function linkOf(payload: unknown): string {
  const packed = deflateSync(new TextEncoder().encode(JSON.stringify(payload)));
  const code = btoa(String.fromCharCode(...packed))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
  return `#run=${code}`;
}

test('a link from the runner gives the stages done and their attempts, as the attempts table takes them', () => {
  const report = reportOf(lab, link);
  expect(report?.passed).toEqual(
    new Map([
      ['stg_count1', null],
      ['stg_review', { caught: ['tst_eeeeee'], total: 2 }],
    ]),
  );
  expect(report?.attempts).toEqual([
    {
      id: '0b7f2f4e-5d3c-4e1a-9a52-7c6f0e2d8b11',
      stage_id: 'stg_review',
      stage_version: 'v1',
      kind: 'run',
      tests_passed: 1,
      tests_total: 1,
      checks_passed: 1,
      checks_total: 2,
      hint: null,
      caught: null,
      problems: null,
      seconds: 42,
      happened_at: '2026-10-18T16:00:00.000Z',
      day: '2026-10-18',
    },
    {
      id: '5a0c7d2b-9e41-4f6a-8c3d-2b1e0f9a7c64',
      stage_id: 'stg_review',
      stage_version: 'v1',
      kind: 'pass',
      tests_passed: null,
      tests_total: null,
      checks_passed: null,
      checks_total: null,
      hint: null,
      caught: ['tst_eeeeee'],
      problems: 2,
      seconds: 8,
      happened_at: '2026-10-18T16:00:08.000Z',
      day: '2026-10-18',
    },
  ]);
});

test('an address without a link from the runner carries nothing', () => {
  expect(reportOf(lab, '')).toBeNull();
  expect(reportOf(lab, '#hints')).toBeNull();
  expect(reportOf(lab, '#run=not base64!')).toBeNull();
  const plain = btoa(JSON.stringify({ format: 1, lab: 'lab_tally1', passed: {}, attempts: [] }));
  expect(reportOf(lab, `#run=${plain.replace(/=+$/, '')}`)).toBeNull();
});

test('a link longer than any the runner writes is ignored', () => {
  const runs = (count: number) =>
    Array.from({ length: count }, (_, index) => [
      crypto.randomUUID(),
      'stg_count1',
      'v1',
      'run',
      [0, 2],
      null,
      null,
      30,
      `2026-10-18T16:${String(index).padStart(2, '0')}:00.000Z`,
      '2026-10-18',
    ]);
  const carrying = (count: number) =>
    linkOf({ format: 1, lab: 'lab_tally1', passed: { stg_count1: null }, attempts: runs(count) });
  const long = carrying(59);
  expect(long.length).toBeGreaterThan(2000);
  expect(reportOf(lab, long)).toBeNull();
  expect(reportOf(lab, carrying(40))?.attempts).toHaveLength(40);
});

test("a link to another lab, or with anything that doesn't hold up, is ignored whole", () => {
  const good = {
    format: 1,
    lab: 'lab_tally1',
    passed: { stg_count1: null },
    attempts: [
      [
        '0b7f2f4e-5d3c-4e1a-9a52-7c6f0e2d8b11',
        'stg_count1',
        'v1',
        'run',
        [2, 2],
        null,
        null,
        5,
        '2026-10-18T16:00:00.000Z',
        '2026-10-18',
      ],
    ],
  };
  expect(reportOf(lab, linkOf(good))?.attempts).toHaveLength(1);
  const attempt = good.attempts[0] as unknown[];
  const changed = (at: number, value: unknown) => ({
    ...good,
    attempts: [attempt.map((each, index) => (index === at ? value : each))],
  });
  for (const bad of [
    { ...good, lab: 'lab_other1' },
    { ...good, format: 2 },
    { ...good, passed: { stg_nowhere: null } },
    // A Catch stage is done only with its review, and a review names only its problems' checks.
    { ...good, passed: { stg_review: null } },
    { ...good, passed: { stg_review: { caught: ['tst_zzzzzz'], problems: 2 } } },
    changed(0, 'not an id'),
    changed(1, 'stg_nowhere'),
    changed(3, 'hint'),
    changed(4, [3, 2]),
    changed(7, 3601),
    changed(8, 'yesterday'),
    changed(9, '18 October'),
    { ...good, attempts: Array.from({ length: 201 }, () => attempt) },
  ]) {
    expect(reportOf(lab, linkOf(bad))).toBeNull();
  }
});

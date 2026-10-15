import { fileURLToPath } from 'node:url';
import type { RunResult, TestResult } from '@sulba/lab/protocol';
import { beforeAll, describe, expect, it } from 'vitest';
import { type Draft, judge, messagesOf, parseReply, replySchema, withBug } from './draft.ts';
import { faults } from './faults.ts';
import { loadCourse, type Stage } from './load.ts';

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const checks = [
  { id: 'tst_demo06', name: 'Most votes first' },
  { id: 'tst_demo07', name: 'Leaves the list of votes as it was' },
];
let stage: Stage;

beforeAll(async () => {
  const { course } = await loadCourse(fixtures, 'demo');
  const found = course?.levels[0]?.modules[0]?.labs[0]?.stages.find(
    (each) => each.slug === 'check',
  );
  if (!found) throw new Error("The fixture course's Catch stage didn't load.");
  stage = found;
});

const draft = (line: number, bug: string): Draft => ({
  check: 'tst_demo06',
  kind: 'silly-mistake',
  line,
  bug,
  summary: 'The least votes come first.',
});

describe('messagesOf', () => {
  it('asks for bugs by line, against the checks, from the kinds of bug', () => {
    const [system, user] = messagesOf(stage, checks, 6);
    expect(system?.content).toContain("passes the assistant's own tests");
    expect(user?.content).toContain('  9 |     shares = [(choice, share(choices, choice))');
    expect(user?.content).toContain('- tst_demo07: Leaves the list of votes as it was');
    expect(user?.content).toContain('One line per choice');
    for (const fault of faults) expect(user?.content).toContain(`- ${fault.id}: `);
    expect(user?.content).toContain('Write 6 different bugs');
  });

  it('holds the reply to the checks and kinds there are', () => {
    const items = replySchema(checks).properties.drafts.items.properties;
    expect(items.check.enum).toEqual(['tst_demo06', 'tst_demo07']);
    expect(items.kind.enum).toEqual(faults.map((fault) => fault.id));
  });
});

describe('parseReply', () => {
  it('reads the drafts, and refuses a reply that is not what was asked', () => {
    const one = draft(10, 'return sorted(shares, key=lambda pair: (pair[1], pair[0]))');
    expect(parseReply(JSON.stringify({ drafts: [one] }))).toEqual([one]);
    expect(() => parseReply('{"drafts": [{"line": 0}]}')).toThrow();
    expect(() => parseReply('not JSON')).toThrow();
  });
});

describe('withBug', () => {
  it("puts the bug on its line in the line's indent, and gives the edit that fixes it", () => {
    const edited = withBug(
      stage.solution,
      draft(10, 'return sorted(shares, key=lambda pair: (pair[1], pair[0]))'),
    );
    expect(edited).toEqual({
      code: expect.stringContaining(
        '\n    return sorted(shares, key=lambda pair: (pair[1], pair[0]))',
      ),
      edit: {
        replace: 'return sorted(shares, key=lambda pair: (pair[1], pair[0]))',
        with: 'return sorted(shares, key=lambda pair: (-pair[1], pair[0]))',
      },
    });
  });

  it('takes a bug of several lines, in the indent it was written in', () => {
    const edited = withBug(
      stage.solution,
      draft(
        10,
        '    choices.sort()\n    return sorted(shares, key=lambda pair: (-pair[1], pair[0]))',
      ),
    );
    expect('code' in edited && edited.code).toContain(
      '    choices.sort()\n    return sorted(shares, key=lambda pair: (-pair[1], pair[0]))\n',
    );
  });

  it("refuses a bug that changes nothing, isn't on a line of code, or isn't unique", () => {
    const line10 = 'return sorted(shares, key=lambda pair: (-pair[1], pair[0]))';
    expect(withBug(stage.solution, draft(10, line10))).toEqual({
      reason: 'It changes nothing.',
    });
    expect(withBug(stage.solution, draft(5, 'x = 1'))).toEqual({
      reason: 'Its line has no code.',
    });
    expect(withBug(stage.solution, draft(99, 'x = 1'))).toEqual({
      reason: 'Its line has no code.',
    });
    expect(withBug(stage.solution, draft(1, 'choices.sort()'))).toEqual({
      reason: 'Its line is a comment.',
    });
    expect(withBug(stage.solution, draft(10, 'from tally import share'))).toEqual({
      reason: 'Its bug would appear 2 times in the starter.',
    });
  });
});

describe('judge', () => {
  const ids = new Set(['tst_demo06', 'tst_demo07']);
  const test = (id: string, status: TestResult['status']): TestResult => ({
    id,
    name: id,
    status,
    message: null,
    expected: null,
    actual: null,
    location: null,
    output: '',
    note: null,
    durationMs: 1,
  });
  const run = (...tests: TestResult[]): RunResult => ({
    status: 'fail',
    tests,
    problem: null,
    output: '',
    durationMs: 1,
  });

  it('keeps a bug that only one check catches', () => {
    const result = run(test('tst_demo04', 'pass'), test('tst_demo06', 'fail'));
    expect(judge(result, ids)).toEqual({ kept: true, check: 'tst_demo06' });
  });

  it("drops a bug the assistant's tests catch, that no check or two catch, or that doesn't run", () => {
    expect(judge(run(test('tst_demo04', 'fail'), test('tst_demo06', 'fail')), ids)).toEqual({
      kept: false,
      reason: "The assistant's tests catch it.",
    });
    expect(judge(run(test('tst_demo04', 'pass'), test('tst_demo06', 'pass')), ids)).toEqual({
      kept: false,
      reason: 'No check catches it.',
    });
    expect(judge(run(test('tst_demo06', 'fail'), test('tst_demo07', 'error')), ids)).toEqual({
      kept: false,
      reason: '2 checks catch it.',
    });
    const broken = {
      ...run(),
      problem: { kind: 'SyntaxError', message: 'invalid syntax', location: null },
    };
    expect(judge(broken, ids)).toEqual({ kept: false, reason: "It doesn't run: SyntaxError." });
  });
});

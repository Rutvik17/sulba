import { describe, expect, it } from 'vitest';
import {
  blockerProblem,
  pullRequestName,
  pullRequestProblem,
  taskKey,
  taskNumberOf,
  taskTitleProblem,
} from './tasks.ts';

describe('task IDs', () => {
  it('reads a task’s number from its ID, in either case', () => {
    expect(taskKey(7)).toBe('TASK-7');
    expect(taskNumberOf('TASK-7')).toBe(7);
    expect(taskNumberOf('task-12')).toBe(12);
  });

  it('refuses what isn’t a task’s ID', () => {
    for (const key of ['TASK-0', 'TASK-07', 'TASK-', 'SPEC-7', 'TASK-1234567890']) {
      expect(taskNumberOf(key)).toBeNull();
    }
  });
});

describe('taskTitleProblem', () => {
  it('asks for a title of at most 200 characters', () => {
    expect(taskTitleProblem('  ')).toBe('Say what the task is.');
    expect(taskTitleProblem('x'.repeat(201))).toBe('A title has at most 200 characters.');
    expect(taskTitleProblem(' Build the booking API ')).toBeNull();
  });
});

describe('blockerProblem', () => {
  it('asks what blocks a task, in at most 2,000 characters', () => {
    expect(blockerProblem('')).toBe('Say what blocks it.');
    expect(blockerProblem('x'.repeat(2001))).toBe('A note has at most 2,000 characters.');
    expect(blockerProblem('Which payment provider?')).toBeNull();
  });
});

describe('pull requests', () => {
  it('takes a GitHub pull request’s address and names it', () => {
    const address = 'https://github.com/acme-co/booking/pull/12';
    expect(pullRequestProblem(` ${address} `)).toBeNull();
    expect(pullRequestName(address)).toBe('acme-co/booking#12');
  });

  it('refuses any other address', () => {
    for (const address of [
      'https://github.com/acme-co/booking/issues/12',
      'http://github.com/acme-co/booking/pull/12',
      'https://example.com/acme-co/booking/pull/12',
      'https://github.com/acme-co/booking/pull/12/files',
    ]) {
      expect(pullRequestProblem(address)).toBe(
        'A pull request’s address looks like https://github.com/owner/repo/pull/12.',
      );
    }
  });
});

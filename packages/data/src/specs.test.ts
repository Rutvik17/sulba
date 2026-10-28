import { describe, expect, it } from 'vitest';
import { criterionKey, criterionProblem, specKey, specNumberOf, titleProblem } from './specs.ts';

describe('IDs', () => {
  it('name a spec and its criteria', () => {
    expect(specKey(12)).toBe('SPEC-12');
    expect(criterionKey(12, 3)).toBe('SPEC-12/AC-3');
  });

  it('are read back from an address, in either case', () => {
    expect(specNumberOf('SPEC-12')).toBe(12);
    expect(specNumberOf('spec-7')).toBe(7);
  });

  it('are read back only when they are a spec’s', () => {
    for (const key of [
      'SPEC-0',
      'SPEC-012',
      'SPEC-',
      'SPEC-1/AC-2',
      'TASK-4',
      'members',
      'SPEC-1234567890',
    ]) {
      expect(specNumberOf(key)).toBeNull();
    }
  });
});

describe('titleProblem', () => {
  it('asks for a title of at most 200 characters', () => {
    expect(titleProblem('Retry failed payments')).toBeNull();
    expect(titleProblem('  ')).toBe('Give the spec a title.');
    expect(titleProblem('a'.repeat(201))).toBe('A title has at most 200 characters.');
    expect(titleProblem(` ${'a'.repeat(200)} `)).toBeNull();
  });
});

describe('criterionProblem', () => {
  it('asks for wording of at most 1,000 characters', () => {
    expect(criterionProblem('When a payment fails, the system shall retry it once')).toBeNull();
    expect(criterionProblem('')).toBe('Write what must be true.');
    expect(criterionProblem('a'.repeat(1001))).toBe('A criterion has at most 1,000 characters.');
  });
});

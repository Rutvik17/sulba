import { expect, test } from 'vitest';
import { languageOf } from './language.ts';

test("a stage's file is read in the language its name says", () => {
  expect(languageOf('stream.ts')).toBe('typescript');
  expect(languageOf('limiter.go')).toBe('go');
  expect(languageOf('Dockerfile')).toBe('dockerfile');
  expect(languageOf('app.py')).toBe('python');
});

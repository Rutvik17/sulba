import { expect, test } from 'vitest';
import { appPath, signInPath } from './session';

test('sign-in sends a person back to the page they came from', () => {
  expect(signInPath(appPath)).toBe('/sign-in/?next=%2Fapp%2F');
  expect(signInPath('/app/specs/?view=open')).toBe(
    '/sign-in/?next=%2Fapp%2Fspecs%2F%3Fview%3Dopen',
  );
});

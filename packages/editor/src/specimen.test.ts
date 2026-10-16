import { expect, test } from 'vitest';
import { specimen } from './specimen.ts';

test('a sample gives each token the colour the editor gives it, line by line', () => {
  expect(specimen('def fit(x=None):  # once\n    return x.shape, "E", 1')).toEqual([
    [
      { text: 'def', role: 'kw' },
      { text: ' ' },
      { text: 'fit', role: 'fn' },
      { text: '(', role: 'op' },
      { text: 'x' },
      { text: '=', role: 'op' },
      { text: 'None', role: 'bi' },
      { text: ')', role: 'op' },
      { text: ':  ' },
      { text: '# once', role: 'com' },
    ],
    [
      { text: '    ' },
      { text: 'return', role: 'kw' },
      { text: ' x' },
      { text: '.', role: 'op' },
      { text: 'shape', role: 'prop' },
      { text: ',', role: 'op' },
      { text: ' ' },
      { text: '"E"', role: 'str' },
      { text: ',', role: 'op' },
      { text: ' ' },
      { text: '1', role: 'num' },
    ],
  ]);
});

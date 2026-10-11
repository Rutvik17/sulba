import { expect, test } from 'vitest';
import { classes } from './classes';

test('classes gives the scoped name of each class asked for', () => {
  expect(classes({ group: '_group_1a', segment: '_segment_2b' }, 'group', 'segment')).toEqual({
    group: '_group_1a',
    segment: '_segment_2b',
  });
});

test('a class the stylesheet lacks is an error', () => {
  expect(() => classes({ group: '_group_1a' }, 'group', 'segment')).toThrow(
    'The stylesheet has no .segment class',
  );
});

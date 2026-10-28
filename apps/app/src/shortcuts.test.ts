import { expect, test } from 'vitest';
import { onMac, press, stepOf, stepsOf, typesText } from './shortcuts';

const shortcuts = [['g', 's'], ['g', 'e'], ['c'], ['?'], ['mod+k']] as const;

const key = (key: string, held: { meta?: boolean; ctrl?: boolean; alt?: boolean } = {}) => ({
  key,
  metaKey: held.meta ?? false,
  ctrlKey: held.ctrl ?? false,
  altKey: held.alt ?? false,
});

test('Cmd is the shortcut key on Apple devices and Ctrl is elsewhere', () => {
  expect(onMac('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')).toBe(true);
  expect(onMac('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)')).toBe(true);
  expect(onMac('Mozilla/5.0 (Windows NT 10.0; Win64; x64)')).toBe(false);
  expect(onMac('Mozilla/5.0 (X11; Linux x86_64)')).toBe(false);
});

test('a press is its key in lower case, with mod+ for the platform’s shortcut key', () => {
  expect(stepOf(key('G'), false)).toBe('g');
  expect(stepOf(key('?'), false)).toBe('?');
  expect(stepOf(key('k', { ctrl: true }), false)).toBe('mod+k');
  expect(stepOf(key('k', { meta: true }), true)).toBe('mod+k');
});

test('a press no shortcut uses makes no step', () => {
  expect(stepOf(key('Shift'), false)).toBeNull();
  expect(stepOf(key('ArrowDown'), false)).toBeNull();
  expect(stepOf(key('k', { alt: true }), false)).toBeNull();
  // Ctrl on a Mac edits text, and the Windows key belongs to the system.
  expect(stepOf(key('k', { ctrl: true }), true)).toBeNull();
  expect(stepOf(key('k', { meta: true }), false)).toBeNull();
});

test('only a shortcut without Cmd or Ctrl is typing', () => {
  expect(typesText('c')).toBe(true);
  expect(typesText('mod+k')).toBe(false);
});

test('a key completes a shortcut of one at once', () => {
  expect(press([], 'c', shortcuts)).toEqual({ done: ['c'], pending: [] });
  expect(press([], 'mod+k', shortcuts)).toEqual({ done: ['mod+k'], pending: [] });
});

test('a sequence waits after its first key and completes on its second', () => {
  const first = press([], 'g', shortcuts);
  expect(first).toEqual({ done: null, pending: ['g'] });
  expect(press(first.pending, 'e', shortcuts)).toEqual({ done: ['g', 'e'], pending: [] });
});

test('a key that doesn’t continue the sequence starts again on its own', () => {
  expect(press(['g'], 'c', shortcuts)).toEqual({ done: ['c'], pending: [] });
  expect(press(['g'], 'g', shortcuts)).toEqual({ done: null, pending: ['g'] });
  expect(press(['g'], 'x', shortcuts)).toEqual({ done: null, pending: [] });
  expect(press([], 'x', shortcuts)).toEqual({ done: null, pending: [] });
});

test('keys show as the caps to press', () => {
  expect(stepsOf(['g', 's'], false)).toEqual([['G'], ['S']]);
  expect(stepsOf(['mod+k'], true)).toEqual([['⌘', 'K']]);
  expect(stepsOf(['mod+k'], false)).toEqual([['Ctrl', 'K']]);
  expect(stepsOf(['?'], false)).toEqual([['?']]);
});

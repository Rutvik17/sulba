// Keyboard shortcuts (decision record 53): a key, a sequence such as G then S, or Cmd on a Mac and
// Ctrl elsewhere with a key. A shortcut is its steps, each a key as the browser names it, lower
// case, with "mod+" before a key pressed with Cmd or Ctrl: ['g', 's'], ['?'], ['mod+k'].
import type { Steps } from '@sulba/ui/keys';

export type Shortcut = readonly string[];

/** How long a sequence waits for its next key. */
export const sequenceTimeout = 1000;

/** Whether this is a Mac, an iPhone or an iPad, where Cmd is the shortcut key and Ctrl isn't. */
export function onMac(userAgent: string): boolean {
  return /Mac|iPhone|iPad|iPod/.test(userAgent);
}

type Press = Pick<KeyboardEvent, 'key' | 'metaKey' | 'ctrlKey' | 'altKey'>;

/**
 * The step a key press makes, or null for a press no shortcut uses: a key that types nothing,
 * such as Shift or an arrow, or one held with Alt or with the other platform's modifier.
 */
export function stepOf(press: Press, mac: boolean): string | null {
  if (press.altKey || [...press.key].length !== 1) return null;
  if (mac ? press.ctrlKey : press.metaKey) return null;
  const key = press.key.toLowerCase();
  return (mac ? press.metaKey : press.ctrlKey) ? `mod+${key}` : key;
}

/** A key that types: a shortcut of one only works where it can't be text. */
export function typesText(step: string): boolean {
  return !step.startsWith('mod+');
}

/**
 * Where the keyboard's focus means a key press is text or belongs to an open control: a field, an
 * editor, a dialog, a menu or a list.
 */
const taken = [
  'input',
  'textarea',
  'select',
  '[contenteditable]:not([contenteditable="false"])',
  '[role="textbox"]',
  '[role="combobox"]',
  '[role="dialog"]',
  '[role="alertdialog"]',
  '[role="menu"]',
  '[role="listbox"]',
].join(', ');

export function focusTaken(target: EventTarget | null): boolean {
  return target instanceof Element && target.closest(taken) !== null;
}

export interface Pressed {
  /** The shortcut the steps so far complete, if any. */
  readonly done: Shortcut | null;
  /** The steps that begin a sequence and wait for the next key. */
  readonly pending: readonly string[];
}

const startsWith = (shortcut: Shortcut, steps: readonly string[]) =>
  steps.length <= shortcut.length && steps.every((step, index) => shortcut[index] === step);

/**
 * Takes a step after the pending ones. A step that doesn't continue a sequence starts again on its
 * own, so G then G then S is still G then S.
 */
export function press(
  pending: readonly string[],
  step: string,
  shortcuts: readonly Shortcut[],
): Pressed {
  const steps = [...pending, step];
  const done = shortcuts.find(
    (shortcut) => shortcut.length === steps.length && startsWith(shortcut, steps),
  );
  if (done) return { done, pending: [] };
  if (shortcuts.some((shortcut) => startsWith(shortcut, steps)))
    return { done: null, pending: steps };
  return pending.length ? press([], step, shortcuts) : { done: null, pending: [] };
}

/** A shortcut as its keys are shown: ['g', 's'] as G then S, ['mod+k'] as ⌘ K or Ctrl K. */
export function stepsOf(shortcut: Shortcut, mac: boolean): Steps {
  return shortcut.map((step) => {
    const key = step.replace(/^mod\+/, '').toUpperCase();
    return step.startsWith('mod+') ? [mac ? '⌘' : 'Ctrl', key] : [key];
  });
}

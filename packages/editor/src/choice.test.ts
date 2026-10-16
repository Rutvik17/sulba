import { afterEach, beforeEach, expect, test, vi } from 'vitest';

/** The browser's storage, as a map. */
function memoryStorage(): Storage {
  const items = new Map<string, string>();
  return {
    getItem: (key) => items.get(key) ?? null,
    setItem: (key, value) => void items.set(key, value),
    removeItem: (key) => void items.delete(key),
    clear: () => items.clear(),
    key: (index) => [...items.keys()][index] ?? null,
    get length() {
      return items.size;
    },
  };
}

/** choice.ts as a page that has just opened loads it. */
async function openPage() {
  vi.resetModules();
  return import('./choice.ts');
}

beforeEach(() => {
  vi.stubGlobal('localStorage', memoryStorage());
  vi.stubGlobal('window', new EventTarget());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("editors open in Sulba's theme until the learner chooses another", async () => {
  const { chosenPalette } = await openPage();

  expect(chosenPalette().id).toBe('sulba');
});

test("a choice is kept for the next page, and choosing Sulba's forgets it", async () => {
  const first = await openPage();
  first.choosePalette('dracula');
  expect(localStorage.getItem(first.choiceKey)).toBe('dracula');

  const next = await openPage();
  expect(next.chosenPalette().id).toBe('dracula');
  next.choosePalette('sulba');

  expect(localStorage.getItem(next.choiceKey)).toBeNull();
  expect((await openPage()).chosenPalette().id).toBe('sulba');
});

test('every editor on the page hears of a new choice until it stops listening', async () => {
  const { chosenPalette, choosePalette, onChoice } = await openPage();
  const heard: string[] = [];

  const stop = onChoice(() => heard.push(chosenPalette().id));
  choosePalette('nord');
  stop();
  choosePalette('night-owl');

  expect(heard).toEqual(['nord']);
});

test("a theme the editor doesn't have opens as Sulba's", async () => {
  localStorage.setItem('sulba:editor-theme', 'no-such-theme');

  const { chosenPalette } = await openPage();

  expect(chosenPalette().id).toBe('sulba');
});

test('with storage blocked, a choice lasts until the page is left', async () => {
  const blocked = () => {
    throw new DOMException('The operation is insecure.', 'SecurityError');
  };
  vi.stubGlobal('localStorage', { getItem: blocked, setItem: blocked, removeItem: blocked });
  const { chosenPalette, choosePalette } = await openPage();
  expect(chosenPalette().id).toBe('sulba');

  choosePalette('nord');

  expect(chosenPalette().id).toBe('nord');
  expect((await openPage()).chosenPalette().id).toBe('sulba');
});

// The editor theme a learner chose, kept in this browser so the next lab opens in it. Sulba's is the
// default, so choosing it forgets the choice, as System does for the page's theme. Every editor on
// the page follows the choice as soon as it's made.
import { type Palette, palettes, sulba } from './palettes.ts';

/** Where the browser keeps the chosen theme's id. */
export const choiceKey = 'sulba:editor-theme';

// Sent on the window when the choice changes.
const changed = 'sulba:editor-theme';

let chosen: Palette | undefined;

const byId = (id: string | null) => palettes.find((palette) => palette.id === id) ?? sulba;

/** The palette the learner chose, or Sulba's. */
export function chosenPalette(): Palette {
  if (chosen === undefined) {
    try {
      chosen = byId(localStorage.getItem(choiceKey));
    } catch {
      // Storage is blocked: editors open in Sulba's theme.
      chosen = sulba;
    }
  }
  return chosen;
}

/** Chooses a palette by its id, for every editor on the page and on the pages opened next. */
export function choosePalette(id: string): void {
  chosen = byId(id);
  try {
    if (chosen === sulba) localStorage.removeItem(choiceKey);
    else localStorage.setItem(choiceKey, chosen.id);
  } catch {
    // Storage is blocked: the choice lasts until the page is left.
  }
  window.dispatchEvent(new Event(changed));
}

/** Calls back each time the choice changes, until the function it returns is called. */
export function onChoice(callback: () => void): () => void {
  window.addEventListener(changed, callback);
  return () => window.removeEventListener(changed, callback);
}

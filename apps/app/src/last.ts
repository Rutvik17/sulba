// The workspace this browser opened last, so the app's front door goes back to it. Storage can
// be blocked or full, and then the front door asks instead.
import { localStore } from '@sulba/data/session';

const key = 'sulba:workspace';

export function lastWorkspace(): string | null {
  try {
    return localStore().getItem(key);
  } catch {
    return null;
  }
}

export function rememberWorkspace(slug: string): void {
  try {
    localStore().setItem(key, slug);
  } catch {}
}

/** Forgets the workspace when it was the last one opened, once the person has left it. */
export function forgetWorkspace(slug: string): void {
  try {
    if (localStore().getItem(key) === slug) localStore().removeItem(key);
  } catch {}
}

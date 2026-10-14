// Where the browser keeps a signed-in learner's session, beside the site's other storage. It is read
// here without loading Supabase, so pages and labs load supabase-js only once a session exists.

/** The local storage key that holds the session, and that sign-out removes. */
export const sessionKey = 'sulba:session';

/** This browser's local storage, or a stand-in that keeps nothing when storage is blocked. */
export function localStore(): Pick<Storage, 'getItem' | 'setItem' | 'removeItem'> {
  try {
    return localStorage;
  } catch {
    return { getItem: () => null, setItem: () => undefined, removeItem: () => undefined };
  }
}

/** Whether this browser holds a session. Storage can be blocked, which counts as none. */
export function hasSession(storage: Pick<Storage, 'getItem'>): boolean {
  try {
    return storage.getItem(sessionKey) !== null;
  } catch {
    return false;
  }
}

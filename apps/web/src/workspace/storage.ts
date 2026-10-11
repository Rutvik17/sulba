// What the workspace keeps in this browser: each stage's code and the stages passed. Storage can
// be blocked or cleared, so every read falls back and every write may fail without harm. Accounts
// will keep progress once they exist (Phase 3).
import type { Kept } from './stages';

function read(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key: string, value: string | null) {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    // Not kept: the page goes on working, and forgets on reload.
  }
}

export const kept: Kept & {
  saveCode(stageId: string, code: string | null): void;
  pass(stageId: string): void;
} = {
  code: (stageId) => read(`sulba:code:${stageId}`),
  passed: (stageId) => read(`sulba:passed:${stageId}`) !== null,
  saveCode: (stageId, code) => write(`sulba:code:${stageId}`, code),
  pass: (stageId) => write(`sulba:passed:${stageId}`, '1'),
};

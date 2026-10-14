// What the workspace keeps in this browser: each stage's code, the stages passed, and each
// finished Catch review. Storage can be blocked or cleared, so every read falls back and every
// write may fail without harm. A signed-in learner's passes and reviews also go to their account,
// and come back from it on another device (sync.ts); their code stays here.
import type { Kept, Review } from './stages';

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

/** A review as it was kept, or null if there is none or it can't be read. */
function reviewOf(text: string | null): Review | null {
  if (text === null) return null;
  try {
    const { caught, total } = JSON.parse(text) as Partial<Review>;
    const valid =
      Array.isArray(caught) &&
      caught.every((id) => typeof id === 'string') &&
      Number.isInteger(total);
    return valid ? { caught, total: total as number } : null;
  } catch {
    return null;
  }
}

export const kept: Kept & {
  saveCode(stageId: string, code: string | null): void;
  pass(stageId: string): void;
  /** Keep a Catch review's score, which also passes its stage. */
  finish(stageId: string, review: Review): void;
} = {
  code: (stageId) => read(`sulba:code:${stageId}`),
  passed: (stageId) => read(`sulba:passed:${stageId}`) !== null,
  review: (stageId) => reviewOf(read(`sulba:review:${stageId}`)),
  saveCode: (stageId, code) => write(`sulba:code:${stageId}`, code),
  pass: (stageId) => write(`sulba:passed:${stageId}`, '1'),
  finish: (stageId, review) => {
    write(`sulba:review:${stageId}`, JSON.stringify(review));
    write(`sulba:passed:${stageId}`, '1');
  },
};

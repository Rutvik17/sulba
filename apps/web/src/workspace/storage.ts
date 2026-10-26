// What the workspace keeps in this browser: each stage's code, the stages passed, each finished
// Catch review, each Problem stage's start, plan and time, and each Design stage's attempt.
// Storage can be blocked or cleared, so every read falls back and every write may fail without
// harm. A signed-in learner's passes and reviews also go to their account, and come back from it
// on another device (sync.ts); their code, plans and designs stay here.
import { type DesignState, designOf } from './design';
import { type ProblemState, problemOf } from './problem';
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
  /** A Problem stage's start, plan and time, or null until the learner starts it. */
  problem(stageId: string): ProblemState | null;
  saveProblem(stageId: string, state: ProblemState): void;
  /** A Design stage's latest attempt, or null until the learner starts it. */
  design(stageId: string): DesignState | null;
  saveDesign(stageId: string, state: DesignState): void;
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
  problem: (stageId) => problemOf(read(`sulba:problem:${stageId}`)),
  saveProblem: (stageId, state) => write(`sulba:problem:${stageId}`, JSON.stringify(state)),
  design: (stageId) => designOf(read(`sulba:design:${stageId}`)),
  saveDesign: (stageId, state) => write(`sulba:design:${stageId}`, JSON.stringify(state)),
};

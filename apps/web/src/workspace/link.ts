// A lab that runs on the learner's machine sends what happened there back to its page by a link
// (decision record 28): the runner, sulba.py, puts the stages done there in the link's fragment,
// each Catch review with them, and its attempts since its last link, as the attempts table takes
// them, in JSON compressed with DEFLATE. A fragment never reaches the server. A link that doesn't
// hold up, in any part, is ignored.
import { type Attempt, maxSeconds } from '@sulba/data/outbox';
import { inflateSync } from 'fflate';
import type { LabView, StageView } from '../lib/labs';
import type { Review } from './stages';

export interface Report {
  /** Each stage done on the learner's machine, by id, with a Catch stage's review. */
  readonly passed: ReadonlyMap<string, Review | null>;
  readonly attempts: readonly Attempt[];
}

/** The most attempts a link carries, as the runner writes them. */
const maxAttempts = 200;

/** The longest link the runner writes, so no fragment is longer (sulba.py's MAX_LINK). */
const maxLink = 2000;

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const day = /^\d{4}-\d{2}-\d{2}$/;

/** The text of DEFLATE in base64url, as Python's urlsafe_b64encode writes it, without its padding. */
function unpacked(code: string): string {
  const binary = atob(code.replace(/-/g, '+').replace(/_/g, '/'));
  const packed = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  return new TextDecoder().decode(inflateSync(packed));
}

const isCount = (value: unknown): value is number => Number.isInteger(value) && Number(value) >= 0;

/** How many of a run's tests or checks passed, as [passed, total], or undefined if it isn't one. */
function countOf(value: unknown): readonly [number, number] | null | undefined {
  if (value === null) return null;
  if (!Array.isArray(value) || value.length !== 2) return undefined;
  const [passed, total] = value as unknown[];
  return isCount(passed) && isCount(total) && passed <= total ? [passed, total] : undefined;
}

/** A Catch stage's review, or undefined if it isn't one of this stage's. */
function reviewOf(stage: StageView, value: unknown): Review | null | undefined {
  if (value === null) return stage.kind === 'catch' ? undefined : null;
  if (stage.kind !== 'catch' || typeof value !== 'object') return undefined;
  const { caught, problems } = value as { caught?: unknown; problems?: unknown };
  const checks = new Set(stage.problems.map((problem) => problem.check));
  const valid =
    Array.isArray(caught) &&
    caught.every((id) => typeof id === 'string' && checks.has(id)) &&
    new Set(caught).size === caught.length &&
    problems === stage.problems.length;
  return valid ? { caught: caught as string[], total: problems } : undefined;
}

function attemptOf(lab: LabView, value: unknown): Attempt | undefined {
  if (!Array.isArray(value) || value.length !== 10) return undefined;
  const [id, stageId, version, kind, tests, checks, review, seconds, at, on] = value as unknown[];
  const stage = lab.stages.find((each) => each.id === stageId);
  if (!stage || typeof id !== 'string' || !uuid.test(id)) return undefined;
  if (typeof version !== 'string' || version.length > 64) return undefined;
  if (!isCount(seconds) || seconds > maxSeconds) return undefined;
  if (typeof at !== 'string' || Number.isNaN(Date.parse(at))) return undefined;
  if (typeof on !== 'string' || !day.test(on)) return undefined;
  const ran = countOf(tests);
  const checked = countOf(checks);
  if (ran === undefined || checked === undefined) return undefined;
  const fields = {
    id,
    stage_id: stage.id,
    stage_version: version,
    hint: null,
    seconds,
    happened_at: new Date(at).toISOString(),
    day: on,
  };
  if (kind === 'run' && ran && review === null) {
    return {
      ...fields,
      kind,
      tests_passed: ran[0],
      tests_total: ran[1],
      checks_passed: checked?.[0] ?? null,
      checks_total: checked?.[1] ?? null,
      caught: null,
      problems: null,
    };
  }
  const reviewed = reviewOf(stage, review);
  if (kind !== 'pass' || ran !== null || checked !== null || reviewed === undefined) {
    return undefined;
  }
  return {
    ...fields,
    kind,
    tests_passed: null,
    tests_total: null,
    checks_passed: null,
    checks_total: null,
    caught: reviewed ? [...reviewed.caught] : null,
    problems: reviewed?.total ?? null,
  };
}

/** What a link to this lab's page carries in its fragment, or null when it carries none. */
export function reportOf(lab: LabView, fragment: string): Report | null {
  if (!fragment.startsWith('#run=') || fragment.length > maxLink) return null;
  let payload: unknown;
  try {
    payload = JSON.parse(unpacked(fragment.slice('#run='.length)));
  } catch {
    return null;
  }
  if (typeof payload !== 'object' || payload === null) return null;
  const { format, lab: id, passed, attempts } = payload as Record<string, unknown>;
  if (format !== 1 || id !== lab.id) return null;
  if (typeof passed !== 'object' || passed === null || Array.isArray(passed)) return null;
  const done = new Map<string, Review | null>();
  for (const [stageId, value] of Object.entries(passed)) {
    const stage = lab.stages.find((each) => each.id === stageId);
    const review = stage && reviewOf(stage, value);
    if (review === undefined) return null;
    done.set(stageId, review);
  }
  if (!Array.isArray(attempts) || attempts.length > maxAttempts) return null;
  const taken: Attempt[] = [];
  for (const value of attempts) {
    const attempt = attemptOf(lab, value);
    if (!attempt) return null;
    taken.push(attempt);
  }
  return { passed: done, attempts: taken };
}

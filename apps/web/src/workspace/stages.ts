// What each stage of a lab starts from and runs against. A stage builds on the learner's own code
// from the stages before it, never on the solutions, except after a Catch review that missed a
// problem: then the fixed code carries on.
import { addStarter } from '@sulba/content/runs';
import type { ChartRequest, RunRequest } from '@sulba/lab/protocol';
import type { LabView } from '../lib/labs';

/** A finished Catch review: the ids of the checks the learner's code passed, of how many. */
export interface Review {
  readonly caught: readonly string[];
  readonly total: number;
}

/** What the learner has kept in this browser. */
export interface Kept {
  /** The learner's code for a stage, or null if they haven't changed its opening code. */
  code(stageId: string): string | null;
  passed(stageId: string): boolean;
  /** A Catch stage's finished review, or null until it is finished. */
  review(stageId: string): Review | null;
}

/**
 * The code a stage shows: the learner's own if they have worked on it. Otherwise its starter, below
 * the code carried on from the last earlier stage on the same file, or alone when no stage before
 * made it.
 */
export function codeOf(lab: LabView, index: number, kept: Kept): string {
  const stage = lab.stages[index];
  if (!stage) throw new Error(`The lab has no stage ${index + 1}.`);
  const own = kept.code(stage.id);
  if (own !== null) return own;
  for (let before = index - 1; before >= 0; before--) {
    if (lab.stages[before]?.file === stage.file) {
      return addStarter(carriedOn(lab, before, kept), stage.starter);
    }
  }
  return stage.starter;
}

/**
 * The code a stage passes on to the stages after it: the learner's own, unless the stage is a
 * Catch stage whose review didn't catch every problem, when its fixed code goes on instead.
 */
export function carriedOn(lab: LabView, index: number, kept: Kept): string {
  const stage = lab.stages[index];
  if (!stage) throw new Error(`The lab has no stage ${index + 1}.`);
  if (stage.kind === 'catch') {
    const caught = kept.review(stage.id)?.caught ?? [];
    if (!stage.problems.every((problem) => caught.includes(problem.check))) return stage.solution;
  }
  return codeOf(lab, index, kept);
}

/** The packages a stage's runs load: its own and every earlier stage's, since it runs their code. */
export function packagesOf(lab: LabView, index: number): RunRequest['packages'] {
  return [...new Set(lab.stages.slice(0, index + 1).flatMap((each) => each.packages))];
}

/** The lab's data, the code each earlier stage carried on for its file, and the stage's code. */
function filesOf(lab: LabView, index: number, code: string, kept: Kept): Record<string, string> {
  const stage = lab.stages[index];
  if (!stage) throw new Error(`The lab has no stage ${index + 1}.`);
  const files: Record<string, string> = { ...lab.files };
  for (let before = 0; before < index; before++) {
    const earlier = lab.stages[before];
    if (earlier) files[earlier.file] = carriedOn(lab, before, kept);
  }
  return { ...files, [stage.file]: code };
}

/** A stage's run: the learner's files, with the tests, then a Catch or Ship stage's checks. */
export function runOf(lab: LabView, index: number, code: string, kept: Kept): RunRequest {
  const stage = lab.stages[index];
  if (!stage) throw new Error(`The lab has no stage ${index + 1}.`);
  return {
    files: { ...stage.tests, ...stage.checks, ...filesOf(lab, index, code, kept) },
    tests: [...Object.keys(stage.tests), ...Object.keys(stage.checks)],
    packages: packagesOf(lab, index),
  };
}

/** A stage's chart, drawn with the learner's files, as a run has them. */
export function chartOf(
  lab: LabView,
  index: number,
  code: string,
  kept: Kept,
  values: ChartRequest['values'],
): ChartRequest {
  const chart = lab.stages[index]?.chart;
  if (!chart) throw new Error(`Stage ${index + 1} has no chart.`);
  const files = { ...filesOf(lab, index, code, kept), 'chart.py': chart.code };
  return { files, values, packages: packagesOf(lab, index) };
}

/** A stage's chart before it is passed, drawn with every stage's solution up to it. */
export function previewOf(
  lab: LabView,
  index: number,
  values: ChartRequest['values'],
): ChartRequest {
  const chart = lab.stages[index]?.chart;
  if (!chart) throw new Error(`Stage ${index + 1} has no chart.`);
  const files: Record<string, string> = { ...lab.files };
  for (const stage of lab.stages.slice(0, index + 1)) files[stage.file] = stage.solution;
  return { files: { ...files, 'chart.py': chart.code }, values, packages: packagesOf(lab, index) };
}

/** The first stage is open, and each stage after one the learner has passed. */
export function isOpen(lab: LabView, index: number, kept: Kept): boolean {
  const before = lab.stages[index - 1];
  return index === 0 || (before !== undefined && kept.passed(before.id));
}

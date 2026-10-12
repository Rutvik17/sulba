// What each stage of a lab starts from and runs against. A stage builds on the learner's own code
// from the stages before it, never on the solutions.
import { addStarter } from '@sulba/content/runs';
import type { RunRequest } from '@sulba/lab/protocol';
import type { LabView } from '../lib/labs';

/** What the learner has kept in this browser. */
export interface Kept {
  /** The learner's code for a stage, or null if they haven't changed its opening code. */
  code(stageId: string): string | null;
  passed(stageId: string): boolean;
}

/**
 * The code a stage shows: the learner's own if they have worked on it. Otherwise its starter, below
 * their code from the last earlier stage on the same file, or alone when no stage before made it.
 */
export function codeOf(lab: LabView, index: number, kept: Kept): string {
  const stage = lab.stages[index];
  if (!stage) throw new Error(`The lab has no stage ${index + 1}.`);
  const own = kept.code(stage.id);
  if (own !== null) return own;
  for (let before = index - 1; before >= 0; before--) {
    if (lab.stages[before]?.file === stage.file) {
      return addStarter(codeOf(lab, before, kept), stage.starter);
    }
  }
  return stage.starter;
}

/** The packages a stage's runs load: its own and every earlier stage's, since it runs their code. */
export function packagesOf(lab: LabView, index: number): RunRequest['packages'] {
  return [...new Set(lab.stages.slice(0, index + 1).flatMap((each) => each.packages))];
}

/** A stage's run: the lab's data, the learner's latest code for each earlier file, and the tests. */
export function runOf(lab: LabView, index: number, code: string, kept: Kept): RunRequest {
  const stage = lab.stages[index];
  if (!stage) throw new Error(`The lab has no stage ${index + 1}.`);
  const files: Record<string, string> = { ...lab.files };
  for (let before = 0; before < index; before++) {
    const earlier = lab.stages[before];
    if (earlier) files[earlier.file] = codeOf(lab, before, kept);
  }
  return {
    files: { ...files, ...stage.tests, [stage.file]: code },
    tests: Object.keys(stage.tests),
    packages: packagesOf(lab, index),
  };
}

/** The first stage is open, and each stage after one the learner has passed. */
export function isOpen(lab: LabView, index: number, kept: Kept): boolean {
  const before = lab.stages[index - 1];
  return index === 0 || (before !== undefined && kept.passed(before.id));
}

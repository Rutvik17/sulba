// What a stage's tests run against. A stage builds on the stages before it: their files are
// there as the learner left them, and a stage on a file an earlier stage made adds its starter
// to the end of the learner's code.
import type { RunRequest } from '@sulba/lab/protocol';
import type { Lab, Stage } from './load.ts';

/** The learner's code with a stage's starter added below it. */
export function addStarter(code: string, starter: string): string {
  return `${code.trimEnd()}\n\n\n${starter}`;
}

export interface StageRuns {
  readonly stage: Stage;
  /** The stage as the learner first sees it, built on the earlier stages' solutions. */
  readonly starter: RunRequest;
  /** The stage's solution, built on the earlier stages' solutions. */
  readonly solution: RunRequest;
  /** The earlier stages' tests against this stage's solution, or null for the first stage. */
  readonly earlier: RunRequest | null;
}

export function stageRuns(lab: Lab): StageRuns[] {
  return lab.stages.map((stage, index) => {
    const before = lab.stages.slice(0, index);
    const files: Record<string, string> = {};
    for (const set of lab.data) files[`data/${set.file}`] = set.text;
    for (const each of before) files[each.file] = each.solution;
    for (const [name, text] of Object.entries(stage.tests)) files[`tests/${name}`] = text;
    const previous = files[stage.file];
    const starter = previous === undefined ? stage.starter : addStarter(previous, stage.starter);
    const packages = [...new Set([...before, stage].flatMap((each) => each.packages))];
    const tests = Object.keys(stage.tests).map((name) => `tests/${name}`);
    const solution = { ...files, [stage.file]: stage.solution };

    // Earlier stages' tests go in a folder each, since two stages may name a test file alike.
    const earlierTests: Record<string, string> = {};
    for (const each of before) {
      for (const [name, text] of Object.entries(each.tests)) {
        earlierTests[`tests/${each.slug}/${name}`] = text;
      }
    }
    return {
      stage,
      starter: { files: { ...files, [stage.file]: starter }, tests, packages },
      solution: { files: solution, tests, packages },
      earlier: before.length
        ? { files: { ...solution, ...earlierTests }, tests: Object.keys(earlierTests), packages }
        : null,
    };
  });
}

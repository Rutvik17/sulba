// What each stage of a lab starts from and runs against. A stage builds on the learner's own code
// from the stages before it, never on the solutions, with two exceptions: after a Catch review that
// missed a problem, the fixed code carries on, and a stage passed on another device carries on its
// solution, since the learner's code stays on the device it was written on.
import { addStarter } from '@sulba/content/runs';
import { type MachineStage, machineDownload, machineStage } from '@sulba/lab/machine';
import type { ChartRequest, RunRequest } from '@sulba/lab/protocol';
import type { LabView, StageView } from '../lib/labs';

/**
 * The text of each of a lab's datasets and references, by its path in a run, such as
 * `data/votes.csv`.
 */
export type LabData = Readonly<Record<string, string>>;

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
 * Catch stage whose review didn't catch every problem, or a stage passed without its code in this
 * browser, when its solution goes on instead.
 */
export function carriedOn(lab: LabView, index: number, kept: Kept): string {
  const stage = lab.stages[index];
  if (!stage) throw new Error(`The lab has no stage ${index + 1}.`);
  if (stage.kind === 'catch') {
    const caught = kept.review(stage.id)?.caught ?? [];
    if (!stage.problems.every((problem) => caught.includes(problem.check))) return stage.solution;
  }
  if (kept.passed(stage.id) && kept.code(stage.id) === null) return stage.solution;
  return codeOf(lab, index, kept);
}

/** The packages a stage's runs load: its own and every earlier stage's, since it runs their code. */
export function packagesOf(lab: LabView, index: number): RunRequest['packages'] {
  return [...new Set(lab.stages.slice(0, index + 1).flatMap((each) => each.packages))];
}

/** The lab's data, the code each earlier stage carried on for its file, and the stage's code. */
function filesOf(
  lab: LabView,
  data: LabData,
  index: number,
  code: string,
  kept: Kept,
): Record<string, string> {
  const stage = lab.stages[index];
  if (!stage) throw new Error(`The lab has no stage ${index + 1}.`);
  const files: Record<string, string> = { ...data };
  for (let before = 0; before < index; before++) {
    const earlier = lab.stages[before];
    if (earlier) files[earlier.file] = carriedOn(lab, before, kept);
  }
  return { ...files, [stage.file]: code };
}

/** A stage's run: the learner's files, with the tests, then a Catch or Ship stage's checks. */
export function runOf(
  lab: LabView,
  data: LabData,
  index: number,
  code: string,
  kept: Kept,
): RunRequest {
  const stage = lab.stages[index];
  if (!stage) throw new Error(`The lab has no stage ${index + 1}.`);
  return {
    files: { ...stage.tests, ...stage.checks, ...filesOf(lab, data, index, code, kept) },
    tests: [...Object.keys(stage.tests), ...Object.keys(stage.checks)],
    packages: packagesOf(lab, index),
  };
}

/**
 * The lab's download as it stands at a stage (decision record 25): the learner's files and the
 * lab's data, as the stage's run has them, beside the files of the lab's project. The lab's
 * references stay out, as its tests do, since only the tests read them.
 */
export function downloadOf(
  lab: LabView,
  data: LabData,
  index: number,
  code: string,
  kept: Kept,
  project: Readonly<Record<string, string>>,
): Record<string, string> {
  const files = filesOf(lab, data, index, code, kept);
  for (const { path } of lab.references) delete files[path];
  return { ...project, ...files };
}

/** A stage as a machine lab's download holds it, with its checks' text in `plain` words. */
function machineStageOf(stage: StageView, plain: (html: string) => string): MachineStage {
  if (stage.kind === 'problem') throw new Error(`${stage.slug} is a Problem stage.`);
  const checks =
    stage.kind === 'catch'
      ? stage.problems.map(({ check, title }) => ({ id: check, title, requires: '', failure: '' }))
      : stage.shipChecks.map(({ check, title, requires, failure }) => ({
          id: check,
          title: plain(title),
          requires: plain(requires),
          failure: plain(failure),
        }));
  return machineStage({
    id: stage.id,
    version: stage.version,
    slug: stage.slug,
    title: stage.title,
    kind: stage.kind,
    file: stage.file,
    starter: stage.starter,
    tests: { ...stage.tests, ...stage.checks },
    checks,
    fixed: stage.kind === 'catch' ? stage.solution : null,
  });
}

/**
 * A machine lab's download (decision record 28), opening at the first stage not yet done: the
 * lab's project with its runner, its data, and the learner's files as that stage opens them. The
 * learner's code stays on their machine, so the stages done before it carry on their solutions.
 * `page` is the lab's page, where the runner's links lead, and `plain` turns a line of prose into
 * the plain words a terminal shows.
 */
export function machineDownloadOf(
  lab: LabView,
  data: LabData,
  kept: Kept,
  project: Readonly<Record<string, string>>,
  page: string,
  plain: (html: string) => string,
): Record<string, string> {
  const next = lab.stages.findIndex((stage) => !kept.passed(stage.id));
  const start = next >= 0 ? next : lab.stages.length - 1;
  const files = filesOf(lab, data, start, codeOf(lab, start, kept), kept);
  for (const path of Object.keys(data)) delete files[path];
  const stages = lab.stages.map((stage) => machineStageOf(stage, plain));
  return machineDownload({
    project,
    data,
    files,
    lab: {
      id: lab.id,
      title: lab.title,
      page,
      start,
      data: lab.data.map(({ path }) => path),
      fetch: lab.fetch.flatMap((source) => source.files),
      model: lab.model ? { title: lab.model.title, ...lab.model.file } : null,
      stages,
    },
  });
}

/** A stage's chart, drawn with the learner's files, as a run has them. */
export function chartOf(
  lab: LabView,
  data: LabData,
  index: number,
  code: string,
  kept: Kept,
  values: ChartRequest['values'],
): ChartRequest {
  const chart = lab.stages[index]?.chart;
  if (!chart) throw new Error(`Stage ${index + 1} has no chart.`);
  const files = { ...filesOf(lab, data, index, code, kept), 'chart.py': chart.code };
  return { files, values, packages: packagesOf(lab, index) };
}

/** A stage's chart before it is passed, drawn with every stage's solution up to it. */
export function previewOf(
  lab: LabView,
  data: LabData,
  index: number,
  values: ChartRequest['values'],
): ChartRequest {
  const chart = lab.stages[index]?.chart;
  if (!chart) throw new Error(`Stage ${index + 1} has no chart.`);
  const files: Record<string, string> = { ...data };
  for (const stage of lab.stages.slice(0, index + 1)) files[stage.file] = stage.solution;
  return { files: { ...files, 'chart.py': chart.code }, values, packages: packagesOf(lab, index) };
}

/** The first stage is open, and each stage after one the learner has passed. */
export function isOpen(lab: LabView, index: number, kept: Kept): boolean {
  const before = lab.stages[index - 1];
  return index === 0 || (before !== undefined && kept.passed(before.id));
}

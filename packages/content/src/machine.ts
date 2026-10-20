// The labs that run on the learner's machine (decision record 28). Their runs and figures go to
// CPython in each lab's own project, and CI runs their downloads on Windows, macOS and Linux.
import { join } from 'node:path';
import { type MachineLab, type MachineStage, machineStage } from '@sulba/lab/machine';
import type { Course, Lab, Stage } from './load.ts';
import { testFiles } from './runs.ts';

export interface PlacedLab {
  readonly lab: Lab;
  /** The lab's folder, from the folder of courses, as problems name it. */
  readonly path: string;
  /** The lab's project's folder on disk, whose environment its runs and figures use. */
  readonly project: string;
}

/** Each lab that runs on the learner's machine, in the courses read from the folder `root`. */
export function machineLabs(root: string, courses: readonly Course[]): PlacedLab[] {
  return courses.flatMap((course) =>
    course.levels.flatMap((level) =>
      level.modules.flatMap((module) =>
        module.labs
          .filter((lab) => lab.runs === 'machine')
          .map((lab) => {
            const path = `${course.slug}/modules/${module.slug}/labs/${lab.slug}`;
            return { lab, path, project: join(root, path, 'project') };
          }),
      ),
    ),
  );
}

/**
 * A stage as a download's lab.json holds it. The text of its checks is the course files' own,
 * figures and all: the site's download renders it, and CI's runs read only the checks' ids.
 */
function stageOf(stage: Stage): MachineStage {
  // The content check keeps Problem stages out of machine labs.
  if (stage.kind === 'problem') throw new Error(`${stage.slug} is a Problem stage.`);
  const checks =
    stage.kind === 'catch'
      ? stage.problems.map(({ check, title }) => ({ id: check, title, requires: '', failure: '' }))
      : stage.shipChecks.map(({ check, title, requires, failure }) => ({
          id: check,
          title,
          requires,
          failure,
        }));
  return machineStage({
    id: stage.id,
    version: stage.version,
    slug: stage.slug,
    title: stage.title,
    kind: stage.kind,
    file: stage.file,
    starter: stage.starter,
    tests: testFiles(stage),
    checks,
    fixed: stage.kind === 'catch' ? stage.solution : null,
  });
}

/** A machine lab as its download's lab.json holds it, opening at stage `start`. */
export function machineLabOf(lab: Lab, page: string, start: number): Omit<MachineLab, 'format'> {
  return {
    id: lab.id,
    title: lab.title,
    page,
    start,
    data: lab.data.map((set) => `data/${set.file}`),
    fetch: lab.fetch.flatMap((source) => source.files),
    models: lab.models.map(({ title, kind, file }) => ({ title, kind, ...file })),
    stages: lab.stages.map(stageOf),
  };
}

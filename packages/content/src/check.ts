// Checks across every course: no two things share an id, and every stage works. A stage works
// when its solution passes its own tests and every earlier stage's, its starter fails at least
// one test, and each of its tests has an id of its own.
import { type RunRequest, type RunResult, statusOf } from '@sulba/lab/protocol';
import { idPattern } from './ids.ts';
import type { Course, Problem } from './load.ts';
import { type StageRuns, stageRuns } from './runs.ts';

/** Runs requests in one runtime and returns their results in the same order. */
export type Runner = (requests: readonly RunRequest[]) => Promise<readonly RunResult[]>;

interface Placed<T> {
  readonly path: string;
  readonly item: T;
}

function stagesOf(course: Course): Placed<StageRuns>[] {
  return course.levels.flatMap((level) =>
    level.modules.flatMap((module) =>
      module.labs.flatMap((lab) =>
        stageRuns(lab).map((runs) => ({
          path: `${course.slug}/modules/${module.slug}/labs/${lab.slug}/stages/${runs.stage.slug}`,
          item: runs,
        })),
      ),
    ),
  );
}

export function duplicateIds(courses: readonly Course[]): Problem[] {
  const seen = new Map<string, string>();
  const problems: Problem[] = [];
  const note = (id: string, path: string) => {
    const first = seen.get(id);
    if (first) problems.push({ path, message: `The id ${id} is already used by ${first}.` });
    else seen.set(id, path);
  };
  for (const course of courses) {
    note(course.id, `${course.slug}/course.yaml`);
    for (const level of course.levels) {
      note(level.id, `${course.slug}/course.yaml (${level.slug})`);
      for (const module of level.modules) {
        const folder = `${course.slug}/modules/${module.slug}`;
        note(module.id, `${folder}/module.yaml`);
        for (const lab of module.labs) {
          note(lab.id, `${folder}/labs/${lab.slug}/lab.yaml`);
          for (const stage of lab.stages) {
            note(stage.id, `${folder}/labs/${lab.slug}/stages/${stage.slug}/stage.yaml`);
          }
        }
      }
    }
  }
  return problems;
}

function failures(result: RunResult): string {
  if (result.problem) return `${result.problem.kind}: ${result.problem.message}`;
  return result.tests
    .filter((test) => test.status !== 'pass')
    .map((test) => `"${test.name}": ${test.message ?? test.status}`)
    .join('; ');
}

/** Run every stage in one runtime, named in the problems it finds. */
export async function prove(
  courses: readonly Course[],
  runner: Runner,
  runtime: string,
): Promise<Problem[]> {
  const stages = courses.flatMap(stagesOf);
  const requests = stages.flatMap(({ item: runs }) =>
    runs.earlier ? [runs.solution, runs.starter, runs.earlier] : [runs.solution, runs.starter],
  );
  const results = [...(await runner(requests))];
  const problems: Problem[] = [];
  const testIds = new Map<string, string>();
  for (const { path, item } of stages) {
    const solution = results.shift() as RunResult;
    const starter = results.shift() as RunResult;
    const earlier = item.earlier ? (results.shift() as RunResult) : null;
    const problem = (message: string) => problems.push({ path, message: `${runtime}: ${message}` });

    if (statusOf(solution.tests, solution.problem) !== 'pass') {
      problem(`The solution fails: ${failures(solution)}`);
    }
    if (statusOf(starter.tests, starter.problem) === 'pass') {
      problem('The starter passes every test, so the stage asks for nothing.');
    }
    if (earlier && statusOf(earlier.tests, earlier.problem) !== 'pass') {
      problem(`The solution breaks an earlier stage: ${failures(earlier)}`);
    }
    for (const test of solution.tests) {
      if (!test.id || !idPattern('test').test(test.id)) {
        problem(`"${test.name}" needs an id: @pytest.mark.id("tst_" and 6 letters or digits).`);
        continue;
      }
      const first = testIds.get(test.id);
      if (first) problem(`The test id ${test.id} is already used by ${first}.`);
      else testIds.set(test.id, `${path} ("${test.name}")`);
    }
  }
  return problems;
}

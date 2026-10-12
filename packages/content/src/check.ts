// Checks across every course: no two things share an id, and every stage works. A stage works
// when its solution passes its own tests and every earlier stage's, and each of its tests has an id
// of its own. A Build stage's starter fails at least one test. A Catch stage's starter, the
// assistant's code, passes the assistant's tests and fails every hidden check, and fixing any one
// of its problems alone passes that problem's check and no other.
import { type RunRequest, type RunResult, statusOf, type TestResult } from '@sulba/lab/protocol';
import { idPattern } from './ids.ts';
import type { Course, Problem, Stage } from './load.ts';
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

/** A run's results split into a Catch stage's hidden checks and the other tests. */
function split(stage: Stage, result: RunResult): { tests: TestResult[]; checks: TestResult[] } {
  const ids = new Set(stage.problems.map((problem) => problem.check));
  return {
    tests: result.tests.filter((test) => !test.id || !ids.has(test.id)),
    checks: result.tests.filter((test) => test.id && ids.has(test.id)),
  };
}

function names(tests: readonly TestResult[]): string {
  return tests.map((test) => `"${test.name}"`).join(', ');
}

/** The singular or plural of a verb, for one test or several. */
function verb(tests: readonly TestResult[], one: string, many: string): string {
  return tests.length === 1 ? one : many;
}

/** A Catch stage's assistant code and each problem's fix, judged by its checks. */
function catchProblems(
  stage: Stage,
  starter: RunResult,
  fixes: readonly RunResult[],
  problem: (message: string) => void,
) {
  if (starter.problem) {
    problem(`The assistant's code doesn't run: ${failures(starter)}`);
    return;
  }
  const { tests, checks } = split(stage, starter);
  const failing = tests.filter((test) => test.status !== 'pass');
  if (failing.length) {
    problem(
      `The assistant's tests must pass on its code, but ${names(failing)} ${verb(failing, 'fails', 'fail')}.`,
    );
  }
  const passing = checks.filter((check) => check.status === 'pass');
  if (passing.length) {
    problem(
      `${names(passing)} ${verb(passing, 'passes', 'pass')} on the assistant's code, so ${verb(passing, 'it finds', 'they find')} no problem.`,
    );
  }
  for (const [index, each] of stage.problems.entries()) {
    const fix = fixes[index] as RunResult;
    const alone = `Fixing "${each.title}" alone`;
    if (fix.problem) {
      problem(`${alone} stops the code running: ${failures(fix)}`);
      continue;
    }
    const parts = split(stage, fix);
    const broken = parts.tests.filter((test) => test.status !== 'pass');
    if (broken.length) {
      problem(`${alone} fails the assistant's ${verb(broken, 'test', 'tests')} ${names(broken)}.`);
    }
    const own = parts.checks.find((check) => check.id === each.check);
    if (own?.status !== 'pass') problem(`${alone} doesn't pass its check ${each.check}.`);
    const others = parts.checks.filter(
      (check) => check.id !== each.check && check.status === 'pass',
    );
    if (others.length) {
      problem(`${alone} also passes ${names(others)}: each check must find one problem.`);
    }
  }
}

/** Run every stage in one runtime, named in the problems it finds. */
export async function prove(
  courses: readonly Course[],
  runner: Runner,
  runtime: string,
): Promise<Problem[]> {
  const stages = courses.flatMap(stagesOf);
  const requests = stages.flatMap(({ item: runs }) => [
    runs.solution,
    runs.starter,
    ...runs.fixes,
    ...(runs.earlier ? [runs.earlier] : []),
  ]);
  const results = [...(await runner(requests))];
  const problems: Problem[] = [];
  const testIds = new Map<string, string>();
  for (const { path, item } of stages) {
    const solution = results.shift() as RunResult;
    const starter = results.shift() as RunResult;
    const fixes = results.splice(0, item.fixes.length);
    const earlier = item.earlier ? (results.shift() as RunResult) : null;
    const problem = (message: string) => problems.push({ path, message: `${runtime}: ${message}` });

    if (statusOf(solution.tests, solution.problem) !== 'pass') {
      problem(`The solution fails: ${failures(solution)}`);
    }
    if (item.stage.kind === 'catch') {
      catchProblems(item.stage, starter, fixes, problem);
    } else if (statusOf(starter.tests, starter.problem) === 'pass') {
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

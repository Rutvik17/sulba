// Checks every course in a folder: its files against their schemas, every stage in Pyodide and in
// CPython, every stage's prose with the numbers its figures.py gives in each, every chart as each
// draws it, and each lab project's lock against Pyodide's versions and its pyproject.toml. Prints
// each problem and fails if there is one. With `--shard 2/4`, it still checks every file against its
// schema and every project's lock, but runs only the second stage of every four, with that stage's
// figures, prose and chart, so that four checks side by side cover every stage.
import { execFile } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { pyodideFolder } from '@sulba/lab/assemble';
import { chartsInCPython, figuresInCPython, pyodideEngine, runInCPython } from '@sulba/lab/node';
import {
  type Course,
  canonicalName,
  checkCharts,
  computeFigures,
  courseSlugs,
  duplicateIds,
  loadCourse,
  type Problem,
  projectProblems,
  proseProblems,
  prove,
  shard,
} from '../src/index.ts';
import { mathFontCharacters } from '../src/math-font.ts';

const { positionals, values } = parseArgs({
  allowPositionals: true,
  options: { shard: { type: 'string', default: '1/1' } },
});
const [, part = 0, parts = 0] = (/^(\d+)\/(\d+)$/.exec(values.shard) ?? []).map(Number);
if (part < 1 || part > parts)
  throw new Error(`--shard takes a part such as 2/4, not ${values.shard}.`);
const root = resolve(positionals[0] ?? '.');
const courses: Course[] = [];
const problems: Problem[] = [];
for (const slug of await courseSlugs(root)) {
  const loaded = await loadCourse(root, slug);
  problems.push(...loaded.problems);
  if (loaded.course) courses.push(loaded.course);
}
problems.push(...duplicateIds(courses));
const only = shard(courses, part, parts);

/** The Python version and the packages, by canonical name, of the Pyodide the site serves. */
async function pyodideVersions() {
  const lock = JSON.parse(await readFile(join(pyodideFolder, 'pyodide-lock.json'), 'utf8')) as {
    info: { python: string };
    packages: Record<string, { version: string }>;
  };
  const packages = Object.entries(lock.packages).map(([name, { version }]) => [
    canonicalName(name),
    version,
  ]);
  return { python: lock.info.python, packages: new Map(packages as [string, string][]) };
}

/** Each lab project whose uv.lock no longer matches its pyproject.toml, as `uv lock --check` finds. */
async function staleLocks(courses: readonly Course[]): Promise<Problem[]> {
  const problems: Problem[] = [];
  for (const course of courses) {
    for (const module of course.levels.flatMap((level) => level.modules)) {
      for (const lab of module.labs.filter((each) => each.project['uv.lock'] !== undefined)) {
        const project = `${course.slug}/modules/${module.slug}/labs/${lab.slug}/project`;
        const failed = await new Promise<string | null>((done) => {
          execFile('uv', ['lock', '--check', '--directory', join(root, project)], (error, _, err) =>
            done(error ? err.trim() || error.message : null),
          );
        });
        if (failed) problems.push({ path: `${project}/uv.lock`, message: failed });
      }
    }
  }
  return problems;
}

problems.push(...projectProblems(courses, await pyodideVersions()), ...(await staleLocks(courses)));

// Stages and figures run only once every file is well formed.
if (problems.length === 0) {
  const engine = await pyodideEngine();
  problems.push(
    ...(await prove(courses, async (requests) => requests.map(engine.run), 'Pyodide', only)),
  );
  problems.push(...(await prove(courses, runInCPython, 'CPython', only)));
  const { figures, problems: found } = await computeFigures(
    courses,
    { Pyodide: async (fileSets) => fileSets.map(engine.figures), CPython: figuresInCPython },
    only,
  );
  problems.push(...found, ...proseProblems(courses, figures, mathFontCharacters(), only));
  problems.push(
    ...(await checkCharts(
      courses,
      { Pyodide: async (requests) => requests.map(engine.chart), CPython: chartsInCPython },
      only,
    )),
  );
}

for (const { path, message } of problems) console.error(`${path}: ${message}`);
const of = parts > 1 ? ` (part ${part} of ${parts})` : '';
console.log(`${courses.length} courses, ${only.size} stages${of}, ${problems.length} problems.`);
process.exitCode = problems.length ? 1 : 0;

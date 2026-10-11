// Checks every course in a folder: its files against their schemas, and every stage in Pyodide
// and in CPython. Prints each problem and fails if there is one.
import { readdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pyodideEngine, runInCPython } from '@sulba/lab/node';
import { type Course, duplicateIds, loadCourse, type Problem, prove } from '../src/index.ts';

const root = resolve(process.argv[2] ?? '.');
const courses: Course[] = [];
const problems: Problem[] = [];
for (const entry of await readdir(root, { withFileTypes: true })) {
  if (!entry.isDirectory()) continue;
  const loaded = await loadCourse(root, entry.name);
  problems.push(...loaded.problems);
  if (loaded.course) courses.push(loaded.course);
}
problems.push(...duplicateIds(courses));

// Stages run only once every file is well formed.
if (problems.length === 0) {
  const engine = await pyodideEngine();
  problems.push(...(await prove(courses, async (requests) => requests.map(engine.run), 'Pyodide')));
  problems.push(...(await prove(courses, runInCPython, 'CPython')));
}

const stages = courses.flatMap((course) =>
  course.levels.flatMap((level) =>
    level.modules.flatMap((module) => module.labs.flatMap((lab) => lab.stages)),
  ),
);
for (const { path, message } of problems) console.error(`${path}: ${message}`);
console.log(`${courses.length} courses, ${stages.length} stages, ${problems.length} problems.`);
process.exitCode = problems.length ? 1 : 0;

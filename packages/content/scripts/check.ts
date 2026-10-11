// Checks every course in a folder: its files against their schemas, every stage in Pyodide and in
// CPython, and every stage's prose with the numbers its figures.py gives in each. Prints each
// problem and fails if there is one.
import { resolve } from 'node:path';
import { figuresInCPython, pyodideEngine, runInCPython } from '@sulba/lab/node';
import {
  type Course,
  computeFigures,
  courseSlugs,
  duplicateIds,
  loadCourse,
  type Problem,
  proseProblems,
  prove,
} from '../src/index.ts';
import { mathFontCharacters } from '../src/math-font.ts';

const root = resolve(process.argv[2] ?? '.');
const courses: Course[] = [];
const problems: Problem[] = [];
for (const slug of await courseSlugs(root)) {
  const loaded = await loadCourse(root, slug);
  problems.push(...loaded.problems);
  if (loaded.course) courses.push(loaded.course);
}
problems.push(...duplicateIds(courses));

// Stages and figures run only once every file is well formed.
if (problems.length === 0) {
  const engine = await pyodideEngine();
  problems.push(...(await prove(courses, async (requests) => requests.map(engine.run), 'Pyodide')));
  problems.push(...(await prove(courses, runInCPython, 'CPython')));
  const { figures, problems: found } = await computeFigures(courses, {
    Pyodide: async (fileSets) => fileSets.map(engine.figures),
    CPython: figuresInCPython,
  });
  problems.push(...found, ...proseProblems(courses, figures, mathFontCharacters()));
}

const stages = courses.flatMap((course) =>
  course.levels.flatMap((level) =>
    level.modules.flatMap((module) => module.labs.flatMap((lab) => lab.stages)),
  ),
);
for (const { path, message } of problems) console.error(`${path}: ${message}`);
console.log(`${courses.length} courses, ${stages.length} stages, ${problems.length} problems.`);
process.exitCode = problems.length ? 1 : 0;

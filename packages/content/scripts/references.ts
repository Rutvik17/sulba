// Records every lab's references again and compares them with the recorded files (decision record
// 27): each lab's references/make.py runs with uv, writing into a folder of its own, so it installs
// the library it records with the versions it pins. Prints each problem and fails if there is one.
//
//     node scripts/references.ts <folder of courses>
import { resolve } from 'node:path';
import { type Course, courseSlugs, loadCourse } from '../src/index.ts';
import { recordWithUv, referenceProblems } from '../src/references.ts';

const root = resolve(process.argv[2] ?? '.');
const courses: Course[] = [];
for (const slug of await courseSlugs(root)) {
  const { course } = await loadCourse(root, slug);
  if (course) courses.push(course);
}

const problems = await referenceProblems(root, courses, recordWithUv);

const labs = courses
  .flatMap((course) => course.levels.flatMap((level) => level.modules))
  .flatMap((module) => module.labs)
  .filter((lab) => lab.references.length > 0);
for (const { path, message } of problems) console.error(`${path}: ${message}`);
const files = labs.reduce((total, lab) => total + lab.references.length, 0);
console.log(`${files} references in ${labs.length} labs, ${problems.length} problems.`);
process.exitCode = problems.length ? 1 : 0;

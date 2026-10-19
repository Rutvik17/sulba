// Checks each lab's recorded references (decision records 27 and 30). The lab's references/make.py
// records them again into a folder of its own, reading the lab's data from another, and must make
// the files lab.yaml lists and no others, each the same JSON as the recorded file, with every number
// within 1e-12 of it: a library's results can differ in their last digits from one machine to
// another.
import { execFile } from 'node:child_process';
import { constants } from 'node:fs';
import { copyFile, mkdtemp, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fetchedFolder, fetchedPath } from '@sulba/lab/fetched';
import { difference, partOf } from './difference.ts';
import type { Course, Lab, Problem } from './load.ts';

/**
 * Runs a lab's make.py so that it writes what it records into `folder`, with the lab's data in
 * `data`.
 */
export type Recorder = (script: string, folder: string, data: string) => Promise<void>;

/**
 * Runs make.py with uv, which installs what it pins, such as the library it records. A script that
 * stops fails with the last line it wrote to stderr, which names its error.
 */
export const recordWithUv: Recorder = (script, folder, data) =>
  new Promise((done, fail) => {
    const options = { maxBuffer: 16 * 1024 * 1024 };
    execFile('uv', ['run', script, folder, data], options, (error, _, err) => {
      if (!error) return done();
      fail(new Error(err.trim().split('\n').at(-1) || error.message));
    });
  });

/** How far a number made again may be from the recorded one. */
const tolerance = 1e-12;

/**
 * The problems with the references of every lab in the courses, which sit in `root`. The files
 * machine labs fetch are kept in `fetched`.
 */
export async function referenceProblems(
  root: string,
  courses: readonly Course[],
  record: Recorder,
  fetched = fetchedFolder,
): Promise<Problem[]> {
  const problems: Problem[] = [];
  for (const course of courses) {
    for (const module of course.levels.flatMap((level) => level.modules)) {
      for (const lab of module.labs.filter((each) => each.references.length > 0)) {
        const path = `${course.slug}/modules/${module.slug}/labs/${lab.slug}`;
        const at = `${path}/references`;
        const made = await mkdtemp(join(tmpdir(), 'sulba-references-'));
        const data = await mkdtemp(join(tmpdir(), 'sulba-data-'));
        try {
          const placed = await placeData(lab, data, fetched).catch((error: Error) => error);
          if (placed instanceof Error) {
            problems.push({ path: `${path}/lab.yaml`, message: `fetch: ${placed.message}` });
            continue;
          }
          const script = join(root, at, 'make.py');
          problems.push(...(await labProblems(lab, at, () => record(script, made, data), made)));
        } finally {
          await rm(made, { recursive: true, force: true });
          await rm(data, { recursive: true, force: true });
        }
      }
    }
  }
  return problems;
}

/**
 * Puts the lab's data in `folder`, as a run has it in `data/`: its datasets, and a copy of each
 * file it fetches, kept in `fetched`. A copy, so that a make.py writing to it can't change the
 * file kept; a clone where the system can make one, which is as quick as a link.
 */
async function placeData(lab: Lab, folder: string, fetched: string): Promise<void> {
  for (const set of lab.data) await writeFile(join(folder, set.file), set.text);
  for (const file of lab.fetch.flatMap((source) => source.files)) {
    const kept = await fetchedPath(file, fetched);
    await copyFile(kept, join(folder, file.file), constants.COPYFILE_FICLONE);
  }
}

/** The problems with one lab's references, which `record` makes again into `made`. */
async function labProblems(
  lab: Lab,
  at: string,
  record: () => Promise<void>,
  made: string,
): Promise<Problem[]> {
  try {
    await record();
  } catch (error) {
    return [{ path: `${at}/make.py`, message: `It stopped: ${(error as Error).message}` }];
  }
  const problems: Problem[] = [];
  const files = await readdir(made);
  for (const reference of lab.references) {
    const path = `${at}/${reference.file}`;
    if (!files.includes(reference.file)) {
      problems.push({ path, message: "make.py doesn't record this file." });
      continue;
    }
    let again: unknown;
    try {
      again = JSON.parse(await readFile(join(made, reference.file), 'utf8'));
    } catch (error) {
      const message = `make.py records it as JSON that doesn't parse: ${(error as Error).message}`;
      problems.push({ path, message });
      continue;
    }
    const recorded: unknown = JSON.parse(reference.text);
    const where = difference(again, recorded, tolerance);
    if (where !== null) {
      const now = JSON.stringify(partOf(again, where));
      const was = JSON.stringify(partOf(recorded, where));
      problems.push({
        path,
        message: `make.py records ${where || 'the file'} as ${now} now, not ${was}.`,
      });
    }
  }
  for (const file of files.filter((name) => !lab.references.some((each) => each.file === name))) {
    const message = "make.py records this file, but lab.yaml doesn't list it under references.";
    problems.push({ path: `${at}/${file}`, message });
  }
  return problems;
}

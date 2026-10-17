// A lab's project runs the learner's files on their machine through uv (decision record 25), so it
// installs what the browser runs: the Python version Pyodide runs, each package Pyodide also ships
// at the version Pyodide ships it, and every package the lab's stages load.
import type { Course, Problem } from './load.ts';

/** What the browser runs: Pyodide's Python version, and each package's version by its name. */
export interface PyodideVersions {
  readonly python: string;
  /** Each package Pyodide ships or the site serves beside it, by its canonical name. */
  readonly packages: ReadonlyMap<string, string>;
}

/** A package's name as the standards compare names: lowercase, each run of -, _ and . one -. */
export function canonicalName(name: string): string {
  return name.toLowerCase().replace(/[-_.]+/g, '-');
}

/**
 * Each package a uv.lock pins, by its canonical name, with every version it pins: a lock holds
 * every platform and Python version a project supports, so it can pin a package more than once.
 */
export function lockedVersions(lock: string): Map<string, string[]> {
  const locked = new Map<string, string[]>();
  for (const [, name = '', version = ''] of lock.matchAll(
    /\[\[package\]\]\nname = "([^"]+)"\nversion = "([^"]+)"/g,
  )) {
    const key = canonicalName(name);
    locked.set(key, [...(locked.get(key) ?? []), version]);
  }
  return locked;
}

/** Where each lab's project disagrees with what the browser runs. */
export function projectProblems(courses: readonly Course[], pyodide: PyodideVersions): Problem[] {
  const [major, minor] = pyodide.python.split('.');
  const python = `==${major}.${minor}.*`;
  const problems: Problem[] = [];
  for (const course of courses) {
    for (const module of course.levels.flatMap((level) => level.modules)) {
      for (const lab of module.labs) {
        const lock = lab.project['uv.lock'];
        if (lock === undefined) continue;
        const path = `${course.slug}/modules/${module.slug}/labs/${lab.slug}/project/uv.lock`;
        const note = (message: string) => problems.push({ path, message });
        const required = /^requires-python = "([^"]*)"$/m.exec(lock)?.[1];
        if (required !== python) {
          note(
            `requires-python is ${required ?? 'missing'}, but the browser runs Python ${pyodide.python}: make it ${python}.`,
          );
        }
        const locked = lockedVersions(lock);
        for (const [name, versions] of locked) {
          const shipped = pyodide.packages.get(name);
          for (const version of versions.filter((each) => shipped && each !== shipped)) {
            note(`${name} is locked at ${version}, but the browser runs ${shipped}.`);
          }
        }
        for (const name of new Set(lab.stages.flatMap((stage) => stage.packages))) {
          if (!locked.has(canonicalName(name))) {
            note(`${name} isn't locked, but the lab's stages load it.`);
          }
        }
      }
    }
  }
  return problems;
}

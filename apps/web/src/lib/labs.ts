// The labs the site has a page for, read from the course files (decision record 7). Astro runs the
// loader in Node when it builds or starts, and pages read what it stored, since pages are
// prerendered in workerd, which can't read the repository's files.

import { readdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import Markdoc from '@markdoc/markdoc';
import { type Course, duplicateIds, type Lab, loadCourse, type Stage } from '@sulba/content';
import type { Loader } from 'astro/loaders';

export interface StageView {
  readonly id: string;
  readonly slug: string;
  readonly kind: Stage['kind'];
  readonly title: string;
  readonly file: string;
  readonly packages: Stage['packages'];
  readonly minutes: number;
  readonly version: string;
  /** Prose as HTML, made by Markdoc from files that can hold no HTML of their own. */
  readonly brief: string;
  readonly hints: readonly string[];
  readonly explanation: string;
  readonly starter: string;
  readonly solution: string;
  /** Each test file, by its path in a run, such as `tests/test_model.py`. */
  readonly tests: Readonly<Record<string, string>>;
}

export interface LabView {
  readonly id: string;
  readonly path: string;
  readonly title: string;
  readonly summary: string;
  readonly course: string;
  readonly level: string;
  readonly module: string;
  readonly data: readonly (Omit<Lab['data'][number], 'text'> & { readonly path: string })[];
  /** Each dataset's text, by its path in a run, such as `data/votes.csv`. */
  readonly files: Readonly<Record<string, string>>;
  readonly stages: readonly StageView[];
}

function html(text: string): string {
  return Markdoc.renderers.html(Markdoc.transform(Markdoc.parse(text)));
}

function stageView(stage: Stage): StageView {
  const tests = Object.fromEntries(
    Object.entries(stage.tests).map(([name, text]) => [`tests/${name}`, text]),
  );
  return {
    id: stage.id,
    slug: stage.slug,
    kind: stage.kind,
    title: stage.title,
    file: stage.file,
    packages: stage.packages,
    minutes: stage.minutes,
    version: stage.version,
    brief: html(stage.brief),
    hints: stage.hints.map(html),
    explanation: html(stage.explanation),
    starter: stage.starter,
    solution: stage.solution,
    tests,
  };
}

export function labViews(course: Course): LabView[] {
  return course.levels.flatMap((level) =>
    level.modules.flatMap((module) =>
      module.labs.map((lab) => ({
        id: lab.id,
        path: `${course.slug}/${module.slug}/${lab.slug}`,
        title: lab.title,
        summary: lab.summary,
        course: course.title,
        level: level.title,
        module: module.title,
        data: lab.data.map(({ text: _, ...set }) => ({ ...set, path: `data/${set.file}` })),
        files: Object.fromEntries(lab.data.map((set) => [`data/${set.file}`, set.text])),
        stages: lab.stages.map(stageView),
      })),
    ),
  );
}

/** The folder of courses: the repository's own, or SULBA_COURSES, which the end-to-end tests set. */
function coursesFolder(): string {
  return resolve(process.env.SULBA_COURSES ?? '../../courses');
}

async function loadAll(root: string): Promise<Course[]> {
  const courses: Course[] = [];
  const problems: string[] = [];
  for (const entry of await readdir(root, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const loaded = await loadCourse(root, entry.name);
    problems.push(...loaded.problems.map(({ path, message }) => `${path}: ${message}`));
    if (loaded.course) courses.push(loaded.course);
  }
  problems.push(...duplicateIds(courses).map(({ path, message }) => `${path}: ${message}`));
  if (problems.length) throw new Error(`The courses have problems:\n${problems.join('\n')}`);
  return courses;
}

export function labsLoader(): Loader {
  return {
    name: 'sulba:labs',
    load: async ({ store, watcher }) => {
      const root = coursesFolder();
      const sync = async () => {
        store.clear();
        for (const course of await loadAll(root)) {
          for (const lab of labViews(course)) store.set({ id: lab.path, data: { ...lab } });
        }
      };
      await sync();
      watcher?.add(root);
      watcher?.on('all', (_, path) => {
        if (resolve(path).startsWith(root)) void sync();
      });
    },
  };
}

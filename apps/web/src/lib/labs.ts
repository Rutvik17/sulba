// The labs the site has a page for, read from the course files (decision record 7). Astro runs the
// loader in Node when it builds or starts, and pages read what it stored, since pages are
// prerendered in workerd, which can't read the repository's files.

import { createHash } from 'node:crypto';
import { basename, resolve } from 'node:path';
import {
  type Chart,
  type Course,
  computeFigures,
  courseSlugs,
  duplicateIds,
  fetchedFiles,
  type Lab,
  labFiles,
  loadCourse,
  machineLabs,
  proseProblems,
  renderProse,
  type Stage,
} from '@sulba/content';
import { mathFontCharacters } from '@sulba/content/math-font';
import {
  type Engine,
  figuresInCPython,
  projectRuntime,
  pyodideEngine,
  pyodideRuntime,
  runnerFiles,
} from '@sulba/lab/node';
import type { Loader } from 'astro/loaders';
import { cachedFigures } from './figures-cache';

export interface StageView {
  readonly id: string;
  readonly slug: string;
  readonly kind: Stage['kind'];
  readonly title: string;
  readonly file: string;
  readonly packages: Stage['packages'];
  readonly minutes: number;
  readonly version: string;
  /**
   * Prose as HTML, made by Markdoc from files that can hold no HTML of their own, with formulas as
   * MathML and the numbers from the stage's figures.py.
   */
  readonly brief: string;
  /** What the stage builds on, one line. */
  readonly builds: string;
  readonly hints: readonly string[];
  readonly explanation: string;
  /** A Catch stage's explanation after its problems, when its problems sit inside it. */
  readonly afterProblems: string | null;
  readonly starter: string;
  readonly solution: string;
  /**
   * Each test file, by its path in a run, such as `tests/test_model.py`. In a Catch stage, the
   * assistant's own tests; in a Ship stage, tests the learner sees only by name.
   */
  readonly tests: Readonly<Record<string, string>>;
  /**
   * A Catch or Ship stage's checks, by their path in a run, such as `tests/checks/test_screener.py`.
   * The page has them, as it has a Ship stage's tests, so a learner who reads its source can find
   * them: runs in the browser are practice (decision record 17).
   */
  readonly checks: Readonly<Record<string, string>>;
  /** A Catch stage's problems, in the order its review lists them. Other stages have none. */
  readonly problems: readonly ProblemView[];
  /** A Ship stage's checks before it ships, in the order they show. Other stages have none. */
  readonly shipChecks: readonly ShipCheckView[];
  /** The chart that draws the learner's code once the stage is passed, if it has one. */
  readonly chart: ChartView | null;
  /** A Design stage's follow-up questions, each a line of HTML. Other stages have none. */
  readonly questions: readonly string[];
  /** A Design stage's rubric, in the order the learner marks it. Other stages have none. */
  readonly rubric: readonly RubricPointView[];
  /** How many of a Design stage's rubric points pass it. Other stages have 0. */
  readonly pass: number;
}

export interface RubricPointView {
  /** What a design should do, and what a strong design says to it, each a line of HTML. */
  readonly point: string;
  readonly answer: string;
}

export interface ChartView {
  readonly title: string;
  readonly sliders: Chart['sliders'];
  /** chart.py, which draws the chart with the learner's code. */
  readonly code: string;
}

export interface ProblemView {
  /** The id of the check that finds the problem. */
  readonly check: string;
  readonly title: string;
  /** What the problem would cost, and its fix, as HTML made like the rest of the prose. */
  readonly cost: string;
  readonly fix: string;
}

export interface ShipCheckView {
  /** The id of the check in `checks/`. */
  readonly check: string;
  /** Its title, what it requires and what it says when it fails, each a line of HTML. */
  readonly title: string;
  readonly requires: string;
  readonly failure: string;
}

export interface LabView {
  readonly id: string;
  readonly path: string;
  /**
   * Where its stages run: in this page, or on the learner's machine, from the lab's download, whose
   * runner brings their results back to the page (decision record 28).
   */
  readonly runs: Lab['runs'];
  readonly title: string;
  readonly summary: string;
  readonly course: string;
  readonly level: string;
  readonly module: string;
  /**
   * Each dataset, with its own page for the credit (`url`), its path in a run, such as
   * `data/votes.csv`, and the address the site serves it at, which changes with its text.
   */
  readonly data: readonly (Omit<Lab['data'][number], 'text'> & {
    readonly path: string;
    readonly served: string;
  })[];
  /**
   * Each recorded reference (decision record 27), with its path in a run, such as
   * `references/shares.json`, and the address the site serves it at, which changes with its text.
   */
  readonly references: readonly { readonly path: string; readonly served: string }[];
  /**
   * What a machine lab's runner fetches from each publisher before its first run (decision record
   * 29): the credit, and each file with its address, size and sha256.
   */
  readonly fetch: Lab['fetch'];
  /**
   * The models a machine lab's runner serves on the learner's machine (decision record 34): each
   * one's title, kind and credit, and its file's address, size and sha256.
   */
  readonly models: Lab['models'];
  /**
   * The files a machine lab gives its learner to build on (decision record 37), by their path in
   * the download and in a run. The site serves them with the project's files.
   */
  readonly given: readonly string[];
  /**
   * The files a download of the lab puts beside the learner's (decision record 25), each with its
   * path in the download and the address the site serves it at, which changes with its text. A
   * machine lab's include its runner and the files it gives. None without a project.
   */
  readonly project: readonly { readonly name: string; readonly served: string }[];
  readonly stages: readonly StageView[];
}

/** A review card, as the Review page shows it (decision record 20). */
export interface CardView {
  readonly id: string;
  /** The id of the stage whose pass brings the card into review. */
  readonly stage: string;
  /** Its question and its answer, as HTML made like the rest of the prose. */
  readonly front: string;
  readonly back: string;
}

/**
 * A lab as the site stores it: what its page shows, its datasets' and references' text, the code
 * by others it ports, and its review cards.
 */
export interface LabEntry extends LabView {
  /** Its place in its course, counting every level's modules' labs in the course's order. */
  readonly order: number;
  /** The machine its level needs, which the course's page states before the level begins. */
  readonly levelNeeds: string;
  /** Code by others that the lab ports, which its page credits with its licence's notice. */
  readonly code: Lab['code'];
  /**
   * Each dataset's, reference's and given file's text, by its path in a run, served apart from the
   * lab's page.
   */
  readonly files: Readonly<Record<string, string>>;
  /** Each project file's text, by its name. The site serves it apart from the lab's page too. */
  readonly projectFiles: Readonly<Record<string, string>>;
  readonly cards: readonly CardView[];
}

/**
 * Where the site serves a dataset, a reference or a project file: a folder named for its text, so
 * it can be cached for good.
 */
function servedAt(folder: 'data' | 'references' | 'project', file: string, text: string): string {
  const hash = createHash('sha256').update(text).digest('hex').slice(0, 16);
  return `/${folder}/${hash}/${file}`;
}

type Figures = ReadonlyMap<string, Readonly<Record<string, string>>>;

function stageView(stage: Stage, figures: Figures): StageView {
  const values = figures.get(stage.id) ?? {};
  const html = (text: string) => renderProse(text, values).html;
  const line = (text: string) => renderProse(text, values, { oneLine: true }).html;
  const tests = Object.fromEntries(
    Object.entries(stage.tests).map(([name, text]) => [`tests/${name}`, text]),
  );
  const checks = Object.fromEntries(
    Object.entries(stage.checks).map(([name, text]) => [`tests/checks/${name}`, text]),
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
    builds: line(stage.builds),
    hints: stage.hints.map(html),
    explanation: html(stage.explanation),
    afterProblems: stage.afterProblems === null ? null : html(stage.afterProblems),
    starter: stage.starter,
    solution: stage.solution,
    tests,
    checks,
    problems: stage.problems.map(({ check, title, cost, fix }) => ({
      check,
      title,
      cost: html(cost),
      fix: html(fix),
    })),
    shipChecks: stage.shipChecks.map(({ check, title, requires, failure }) => ({
      check,
      title: line(title),
      requires: line(requires),
      failure: line(failure),
    })),
    chart: stage.chart && {
      title: stage.chart.title,
      sliders: stage.chart.sliders,
      code: stage.chart.code,
    },
    questions: stage.questions.map(line),
    rubric: stage.rubric.map(({ point, answer }) => ({ point: line(point), answer: line(answer) })),
    pass: stage.pass,
  };
}

function cardViews(stage: Stage, figures: Figures): CardView[] {
  const values = figures.get(stage.id) ?? {};
  return stage.cards.map(({ id, front, back }) => ({
    id,
    stage: stage.id,
    front: renderProse(front, values).html,
    back: renderProse(back, values).html,
  }));
}

/**
 * Each of the course's labs as the site stores it, with its stages' figures, and with the runner a
 * machine lab's download carries, each of its files by its path in the download.
 */
export function labEntries(
  course: Course,
  figures: Figures = new Map(),
  runner: Readonly<Record<string, string>> = {},
): LabEntry[] {
  const placed = course.levels.flatMap((level) =>
    level.modules.flatMap((module) => module.labs.map((lab) => ({ level, module, lab }))),
  );
  return placed.map(({ level, module, lab }, order) => {
    const given = Object.fromEntries(lab.given.map(({ file, text }) => [file, text]));
    const project = lab.runs === 'machine' ? { ...lab.project, ...given, ...runner } : lab.project;
    return entryOf(course, level, module, lab, order, project, figures);
  });
}

function entryOf(
  course: Course,
  level: Course['levels'][number],
  module: Course['levels'][number]['modules'][number],
  lab: Lab,
  order: number,
  project: Readonly<Record<string, string>>,
  figures: Figures,
): LabEntry {
  return {
    id: lab.id,
    order,
    path: `${course.slug}/${module.slug}/${lab.slug}`,
    runs: lab.runs,
    title: lab.title,
    summary: lab.summary,
    course: course.title,
    level: level.title,
    levelNeeds: level.needs,
    module: module.title,
    data: lab.data.map(({ text, ...set }) => ({
      ...set,
      path: `data/${set.file}`,
      served: servedAt('data', set.file, text),
    })),
    references: lab.references.map(({ file, text }) => ({
      path: `references/${file}`,
      served: servedAt('references', file, text),
    })),
    fetch: lab.fetch,
    models: lab.models,
    given: lab.given.map((each) => each.file),
    // A file in the runner's folder is served under its own name, one folder below the hash.
    project: Object.entries(project).map(([name, text]) => ({
      name,
      served: servedAt('project', basename(name), text),
    })),
    code: lab.code,
    files: labFiles(lab),
    projectFiles: { ...project },
    stages: lab.stages.map((stage) => stageView(stage, figures)),
    cards: lab.stages.flatMap((stage) => cardViews(stage, figures)),
  };
}

/** The folder of courses: the repository's own, or SULBA_COURSES, which the end-to-end tests set. */
function coursesFolder(): string {
  return resolve(process.env.SULBA_COURSES ?? '../../courses');
}

async function loadAll(root: string): Promise<Course[]> {
  // Courses are checked in full by `pnpm check:content`; the site won't build with a problem.
  const courses: Course[] = [];
  const problems: string[] = [];
  for (const slug of await courseSlugs(root)) {
    const loaded = await loadCourse(root, slug);
    problems.push(...loaded.problems.map(({ path, message }) => `${path}: ${message}`));
    if (loaded.course) courses.push(loaded.course);
  }
  problems.push(...duplicateIds(courses).map(({ path, message }) => `${path}: ${message}`));
  if (problems.length) throw new Error(`The courses have problems:\n${problems.join('\n')}`);
  return courses;
}

/** Where the build keeps the figures it has computed (figures-cache.ts). */
function figuresFolder(): string {
  return resolve('../../node_modules/.cache/sulba-figures');
}

/**
 * Each stage's figures, computed or kept from before, and its prose checked with them: in Pyodide,
 * or for a lab that runs on the learner's machine, in CPython in its own project, with the files it
 * fetches.
 */
async function figuresOf(
  root: string,
  courses: Course[],
  python: () => Promise<Engine>,
): Promise<Figures> {
  const stages = courses.flatMap((course) =>
    course.levels.flatMap((level) =>
      level.modules.flatMap((module) => module.labs.flatMap((lab) => lab.stages)),
    ),
  );
  if (!stages.some((stage) => stage.figures !== null)) return new Map();
  const machine = machineLabs(root, courses);
  const onMachine = new Set(machine.flatMap(({ lab }) => lab.stages.map((stage) => stage.id)));
  const inBrowser = new Set(stages.map(({ id }) => id).filter((id) => !onMachine.has(id)));
  const runtime = await pyodideRuntime();
  const { figures, problems } = await computeFigures(
    courses,
    {
      Pyodide: cachedFigures(figuresFolder(), runtime, async (fileSets) => {
        const engine = await python();
        return fileSets.map(engine.figures);
      }),
    },
    inBrowser,
  );
  for (const { lab, project } of machine) {
    const where = { folder: project, fetched: fetchedFiles(lab) };
    const inProject = await projectRuntime(lab.project['uv.lock'] ?? '', where.fetched);
    const computed = await computeFigures(
      courses,
      {
        CPython: cachedFigures(figuresFolder(), inProject, (fileSets) =>
          figuresInCPython(fileSets, where),
        ),
      },
      new Set(lab.stages.map(({ id }) => id)),
    );
    problems.push(...computed.problems);
    for (const [id, values] of computed.figures) figures.set(id, values);
  }
  problems.push(...proseProblems(courses, figures, mathFontCharacters()));
  if (problems.length) {
    const listed = problems.map(({ path, message }) => `${path}: ${message}`).join('\n');
    throw new Error(`The courses' prose has problems:\n${listed}`);
  }
  return figures;
}

export function labsLoader(): Loader {
  let engine: Promise<Engine> | undefined;
  const python = () => {
    engine ??= pyodideEngine();
    return engine;
  };
  return {
    name: 'sulba:labs',
    load: async ({ store, watcher }) => {
      const root = coursesFolder();
      const sync = async () => {
        const courses = await loadAll(root);
        const figures = await figuresOf(root, courses, python);
        const runner = await runnerFiles();
        store.clear();
        for (const course of courses) {
          for (const lab of labEntries(course, figures, runner))
            store.set({ id: lab.path, data: { ...lab } });
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

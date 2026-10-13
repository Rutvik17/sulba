// Reads a course folder into a typed tree. Every problem found is collected, so one check reports
// them all: a file that breaks its schema, a folder that is listed but missing or present but
// unlisted, a file a stage doesn't use, or prose with a tag Sulba doesn't support.
import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';
import { join, relative, sep } from 'node:path';
import Markdoc from '@markdoc/markdoc';
import { parse } from 'yaml';
import type { z } from 'zod';
import {
  type CatchProblem,
  type ChartFile,
  type CourseFile,
  courseFile,
  type LabFile,
  labFile,
  type ModuleFile,
  moduleFile,
  type ShipCheck,
  type StageFile,
  stageFile,
} from './schema.ts';

export interface Problem {
  /** The file or folder, from the folder of courses. */
  readonly path: string;
  readonly message: string;
}

export type { CatchProblem, ChartFile, ShipCheck } from './schema.ts';

/** A stage's chart: what stage.yaml says of it, and chart.py, which draws it. */
export interface Chart extends ChartFile {
  readonly code: string;
}

export interface Stage extends Omit<StageFile, 'problems' | 'checks' | 'chart'> {
  /** A Catch stage's problems, in the order its review lists them. Other stages have none. */
  readonly problems: readonly CatchProblem[];
  /** A Ship stage's checks before it ships, in the order they show. Other stages have none. */
  readonly shipChecks: readonly ShipCheck[];
  readonly slug: string;
  readonly brief: string;
  /** In the order they open. A stage that needs none has none. */
  readonly hints: readonly string[];
  /**
   * The explanation, in Markdoc: all of it, or in a Catch stage whose problems sit inside it, the
   * part before them.
   */
  readonly explanation: string;
  /** A Catch stage's explanation after its problems, where a line of --- puts them inside it. */
  readonly afterProblems: string | null;
  /** The code this stage starts from: a new file, or code added to the learner's own. */
  readonly starter: string;
  /** The learner's file as it should be once the stage is done. */
  readonly solution: string;
  /**
   * Each test file, by its name in `tests/`. In a Catch stage, the assistant's own tests; in a Ship
   * stage, tests the learner sees only by name.
   */
  readonly tests: Readonly<Record<string, string>>;
  /**
   * A Catch or Ship stage's checks, each file by its name in `checks/`: a Catch stage's hidden
   * checks, or the checks a Ship stage's code must pass before it ships. Other stages have none.
   */
  readonly checks: Readonly<Record<string, string>>;
  /** The stage's figures.py, which computes the numbers its prose shows, if it has one. */
  readonly figures: string | null;
  /** The chart that draws the learner's code once the stage is passed, if it has one. */
  readonly chart: Chart | null;
  /** A hash of every file in the stage, so progress can tell when a stage has changed. */
  readonly version: string;
}

export type Dataset = LabFile['data'][number] & { readonly text: string };

export interface Lab extends Omit<LabFile, 'stages' | 'data'> {
  readonly slug: string;
  readonly data: readonly Dataset[];
  readonly stages: readonly Stage[];
}

export interface Module extends Omit<ModuleFile, 'labs'> {
  readonly slug: string;
  readonly labs: readonly Lab[];
}

export interface Level extends Omit<CourseFile['levels'][number], 'modules'> {
  readonly modules: readonly Module[];
}

export interface Course extends Omit<CourseFile, 'levels'> {
  readonly slug: string;
  readonly levels: readonly Level[];
}

export interface Loaded {
  readonly course: Course | null;
  readonly problems: readonly Problem[];
}

/** Read the course in the folder `slug` inside `root`, the folder of courses. */
export async function loadCourse(root: string, slug: string): Promise<Loaded> {
  const reader = new Reader(root);
  const course = await reader.course(join(root, slug), slug);
  return { course, problems: reader.problems };
}

class Reader {
  readonly problems: Problem[] = [];
  readonly root: string;

  constructor(root: string) {
    this.root = root;
  }

  async course(folder: string, slug: string): Promise<Course | null> {
    const file = await this.yaml(join(folder, 'course.yaml'), courseFile);
    await this.entries(folder, ['course.yaml'], ['modules']);
    const present = await this.folders(join(folder, 'modules'));
    const listed = file?.levels.flatMap((level) => level.modules) ?? [];
    this.matches(join(folder, 'modules'), listed, present, 'a level');
    if (!file) return null;
    const levels: Level[] = [];
    for (const level of file.levels) {
      const modules: Module[] = [];
      for (const name of level.modules) {
        if (!present.includes(name)) continue;
        const module = await this.module(join(folder, 'modules', name), name);
        if (module) modules.push(module);
      }
      levels.push({ ...level, modules });
    }
    return { ...file, slug, levels };
  }

  async module(folder: string, slug: string): Promise<Module | null> {
    const file = await this.yaml(join(folder, 'module.yaml'), moduleFile);
    await this.entries(folder, ['module.yaml'], ['labs']);
    const present = await this.folders(join(folder, 'labs'));
    this.matches(join(folder, 'labs'), file?.labs ?? [], present, 'module.yaml');
    if (!file) return null;
    const labs: Lab[] = [];
    for (const name of file.labs) {
      if (!present.includes(name)) continue;
      const lab = await this.lab(join(folder, 'labs', name), name);
      if (lab) labs.push(lab);
    }
    return { ...file, slug, labs };
  }

  async lab(folder: string, slug: string): Promise<Lab | null> {
    const file = await this.yaml(join(folder, 'lab.yaml'), labFile);
    const hasData = (file?.data.length ?? 0) > 0;
    await this.entries(folder, ['lab.yaml'], hasData ? ['data', 'stages'] : ['stages']);
    const present = await this.folders(join(folder, 'stages'));
    this.matches(join(folder, 'stages'), file?.stages ?? [], present, 'lab.yaml');
    if (!file) return null;
    if (hasData)
      await this.entries(
        join(folder, 'data'),
        file.data.map((set) => set.file),
        [],
      );
    const data: Dataset[] = [];
    for (const set of file.data) {
      const text = await this.text(join(folder, 'data', set.file));
      if (text !== null) data.push({ ...set, text });
    }
    const stages: Stage[] = [];
    for (const name of file.stages) {
      if (!present.includes(name)) continue;
      const stage = await this.stage(join(folder, 'stages', name), name);
      if (!stage) continue;
      // The assistant writes a Catch stage's file, so it starts from the assistant's code alone.
      if (stage.kind === 'catch' && stages.some((earlier) => earlier.file === stage.file)) {
        this.problem(
          join(folder, 'stages', name, 'stage.yaml'),
          `file: A Catch stage's file is the assistant's, so no earlier stage may make ${stage.file}.`,
        );
      }
      stages.push(stage);
    }
    // A chart runs as chart.py beside the learner's files, so no learner's file may take the name.
    if (stages.some((stage) => stage.chart)) {
      for (const stage of stages.filter((each) => each.file === 'chart.py')) {
        this.problem(
          join(folder, 'stages', stage.slug, 'stage.yaml'),
          "file: chart.py is the name a stage's chart runs as, so the learner's file needs another.",
        );
      }
    }
    return { ...file, slug, data, stages };
  }

  async stage(folder: string, slug: string): Promise<Stage | null> {
    const file = await this.yaml(join(folder, 'stage.yaml'), stageFile);
    const hasChecks = file?.kind === 'catch' || file?.kind === 'ship';
    await this.entries(
      folder,
      ['stage.yaml', 'brief.md', 'explanation.md'],
      ['starter', 'solution', 'tests', ...(hasChecks ? ['checks'] : [])],
      ['hints.md', 'figures.py', 'chart.py'],
    );
    if (!file) return null;
    await this.entries(join(folder, 'starter'), [file.file], []);
    await this.entries(join(folder, 'solution'), [file.file], []);
    const present = new Set(((await this.list(folder)) ?? []).map((entry) => entry.name));
    const hasHints = present.has('hints.md');

    const [brief, hints, explanation, starter, solution, tests, checks] = await Promise.all([
      this.prose(join(folder, 'brief.md')),
      hasHints ? this.prose(join(folder, 'hints.md')) : Promise.resolve(''),
      this.prose(join(folder, 'explanation.md')),
      this.text(join(folder, 'starter', file.file)),
      this.text(join(folder, 'solution', file.file)),
      this.testFiles(join(folder, 'tests'), 'A stage needs a test file.'),
      hasChecks
        ? this.testFiles(
            join(folder, 'checks'),
            `A ${file.kind === 'catch' ? 'Catch' : 'Ship'} stage needs a check file.`,
          )
        : Promise.resolve({}),
    ]);
    const figures = present.has('figures.py') ? await this.text(join(folder, 'figures.py')) : null;
    const chart = await this.chart(folder, file.chart, present.has('chart.py'));
    if (brief === null || hints === null || explanation === null) return null;
    if (starter === null || solution === null) return null;
    const hintList = hasHints ? hints.split(/^---$/m).map((hint) => hint.trim()) : [];
    if (hintList.some((hint) => hint === '')) {
      this.problem(join(folder, 'hints.md'), 'Each hint, between lines of ---, needs text.');
    }
    const parts = explanation.split(/^---$/m).map((part) => part.trim());
    if (parts.length > 1) {
      const path = join(folder, 'explanation.md');
      if (file.kind !== 'catch') {
        this.problem(
          path,
          "Only a Catch stage's explanation has a line of ---, where its problems go.",
        );
      } else if (parts.length > 2) {
        this.problem(path, 'An explanation has at most one line of ---, where the problems go.');
      } else if (parts.some((part) => part === '')) {
        this.problem(path, 'The explanation needs text before and after its line of ---.');
      }
    }
    const problems = file.kind === 'catch' ? file.problems : [];
    const shipChecks = file.kind === 'ship' ? file.checks : [];
    if (file.kind === 'catch') this.problemsMatch(folder, problems, starter, checks);
    if (file.kind === 'ship') this.shipChecksMatch(folder, shipChecks, checks);
    const version = hash({
      'stage.yaml': JSON.stringify(file),
      brief,
      hints,
      explanation,
      starter,
      solution,
      ...(figures === null ? {} : { 'figures.py': figures }),
      ...(chart === null ? {} : { 'chart.py': chart.code }),
      ...tests,
      ...Object.fromEntries(Object.entries(checks).map(([name, text]) => [`checks/${name}`, text])),
    });
    return {
      ...file,
      problems,
      shipChecks,
      slug,
      brief,
      hints: hintList,
      explanation: parts[0] ?? '',
      afterProblems: parts[1] ?? null,
      starter,
      solution,
      tests,
      checks,
      figures,
      chart,
      version,
    };
  }

  /**
   * A stage's chart: stage.yaml names it and its sliders, and chart.py draws it, so the stage has
   * both or neither. What chart.py draws is checked by running it.
   */
  async chart(
    folder: string,
    described: ChartFile | undefined,
    drawn: boolean,
  ): Promise<Chart | null> {
    if (!described) {
      if (drawn) this.problem(join(folder, 'chart.py'), 'stage.yaml has no chart for it to draw.');
      return null;
    }
    if (!drawn) {
      this.problem(
        join(folder, 'chart.py'),
        'Missing: stage.yaml has a chart, which chart.py draws.',
      );
      return null;
    }
    const code = await this.text(join(folder, 'chart.py'));
    return code === null ? null : { ...described, code };
  }

  /** The test files in a folder, each by name, which must be test_<name>.py. */
  async testFiles(folder: string, none: string): Promise<Record<string, string>> {
    const names = (await this.files(folder)).sort();
    for (const name of names) {
      if (!/^test_[a-z0-9_]+\.py$/.test(name)) {
        this.problem(join(folder, name), 'A test file is named test_<name>.py.');
      }
    }
    if (names.length === 0) this.problem(folder, none);
    const files: Record<string, string> = {};
    for (const name of names) {
      const text = await this.text(join(folder, name));
      if (text !== null) files[name] = text;
    }
    return files;
  }

  /**
   * A Catch stage's problems and checks match: each problem names a check that `checks/` has, each
   * check belongs to one problem, each edit finds its text in the starter exactly once, and the
   * prose has no tags. Whether each edit fixes its problem alone is proved by running it.
   */
  problemsMatch(
    folder: string,
    problems: readonly CatchProblem[],
    starter: string,
    checks: Readonly<Record<string, string>>,
  ) {
    const path = join(folder, 'stage.yaml');
    this.checksNamed(folder, problems, checks, {
      field: 'problems',
      twice: (id) => `Another problem already names ${id}.`,
      unnamed: (id) => `No problem in stage.yaml names the check ${id}.`,
    });
    problems.forEach((problem, index) => {
      const at = `problems.${index}`;
      const times = starter.split(problem.edit.replace).length - 1;
      if (times !== 1) {
        this.problem(
          path,
          `${at}.edit: The text to replace must appear once in the starter, but appears ${times} times.`,
        );
      }
      for (const field of ['cost', 'fix'] as const)
        this.yamlProse(path, `${at}.${field}`, problem[field]);
    });
  }

  /**
   * A Ship stage's checks in stage.yaml and in `checks/` match: each one listed is in `checks/`,
   * none is listed twice, every check is listed, and the text has no tags.
   */
  shipChecksMatch(
    folder: string,
    listed: readonly ShipCheck[],
    checks: Readonly<Record<string, string>>,
  ) {
    const path = join(folder, 'stage.yaml');
    this.checksNamed(folder, listed, checks, {
      field: 'checks',
      twice: (id) => `${id} is already listed.`,
      unnamed: (id) => `stage.yaml's checks don't list ${id}.`,
    });
    listed.forEach((check, index) => {
      for (const field of ['title', 'requires', 'failure'] as const) {
        this.yamlProse(path, `checks.${index}.${field}`, check[field]);
      }
    });
  }

  /** The entries in stage.yaml and the checks in `checks/` name each other, one to one. */
  checksNamed(
    folder: string,
    named: readonly { readonly check: string }[],
    checks: Readonly<Record<string, string>>,
    say: {
      readonly field: string;
      readonly twice: (id: string) => string;
      readonly unnamed: (id: string) => string;
    },
  ) {
    const path = join(folder, 'stage.yaml');
    const found = new Map<string, string>();
    for (const [name, text] of Object.entries(checks)) {
      for (const [, id] of text.matchAll(/@pytest\.mark\.id\(\s*["'](tst_[0-9a-z]{6})["']\s*\)/g)) {
        found.set(id as string, name);
      }
    }
    named.forEach(({ check }, index) => {
      const at = `${say.field}.${index}.check`;
      if (!found.has(check)) this.problem(path, `${at}: No check in checks/ has the id ${check}.`);
      if (named.findIndex((other) => other.check === check) !== index) {
        this.problem(path, `${at}: ${say.twice(check)}`);
      }
    });
    for (const [id, name] of found) {
      if (!named.some(({ check }) => check === id)) {
        this.problem(join(folder, 'checks', name), say.unnamed(id));
      }
    }
  }

  /** Markdoc in stage.yaml, such as a problem's cost: it may show figures, and has no tags. */
  yamlProse(path: string, at: string, text: string) {
    for (const { error } of Markdoc.validate(Markdoc.parse(text), {})) {
      if (error.id !== 'variable-undefined') this.problem(path, `${at}: ${error.message}`);
    }
  }

  async yaml<T extends z.ZodType>(path: string, schema: T): Promise<z.infer<T> | null> {
    const text = await this.text(path);
    if (text === null) return null;
    let data: unknown;
    try {
      data = parse(text);
    } catch (error) {
      this.problem(path, `Not valid YAML: ${(error as Error).message}`);
      return null;
    }
    const result = schema.safeParse(data);
    if (result.success) return result.data;
    for (const issue of issuesOf(result.error.issues)) {
      const at = issue.path.length ? `${issue.path.join('.')}: ` : '';
      this.problem(path, `${at}${issue.message}`);
    }
    return null;
  }

  /**
   * Prose in Markdoc, with no tags: a tag in the text is a mistake. Its formulas and figures are
   * checked once figures.py has run (`proseProblems`).
   */
  async prose(path: string): Promise<string | null> {
    const text = await this.text(path);
    if (text === null) return null;
    for (const { error } of Markdoc.validate(Markdoc.parse(text), {})) {
      if (error.id !== 'variable-undefined') this.problem(path, error.message);
    }
    if (text.trim() === '') this.problem(path, 'This file needs text.');
    return text;
  }

  async text(path: string): Promise<string | null> {
    try {
      const text = await readFile(path, 'utf8');
      if (text.includes('\r')) this.problem(path, 'Use LF line endings.');
      return text;
    } catch {
      this.problem(path, 'Missing.');
      return null;
    }
  }

  /** The folder holds these files and folders, may hold the optional files, and nothing else. */
  async entries(
    folder: string,
    files: readonly string[],
    folders: readonly string[],
    optional: readonly string[] = [],
  ) {
    const found = await this.list(folder);
    if (!found) return this.problem(folder, 'Missing.');
    for (const entry of found) {
      const expected = entry.isDirectory() ? folders : [...files, ...optional];
      if (!expected.includes(entry.name)) {
        this.problem(join(folder, entry.name), 'Not part of the course: list it or remove it.');
      }
    }
    for (const name of [...files, ...folders]) {
      if (!found.some((entry) => entry.name === name)) this.problem(join(folder, name), 'Missing.');
    }
  }

  /** Folders listed in a YAML file must exist, and each one present must be listed once. */
  matches(folder: string, listed: readonly string[], present: readonly string[], where: string) {
    for (const name of new Set(listed)) {
      if (!present.includes(name))
        this.problem(join(folder, name), `Listed in ${where} but missing.`);
      if (listed.filter((other) => other === name).length > 1) {
        this.problem(join(folder, name), `Listed more than once in ${where}.`);
      }
    }
    for (const name of present) {
      if (!listed.includes(name)) this.problem(join(folder, name), `Not listed in ${where}.`);
    }
  }

  async folders(folder: string): Promise<string[]> {
    return ((await this.list(folder)) ?? [])
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name);
  }

  async files(folder: string): Promise<string[]> {
    return ((await this.list(folder)) ?? [])
      .filter((entry) => entry.isFile())
      .map((entry) => entry.name);
  }

  /** A folder's entries, leaving out hidden ones such as a tool's cache. */
  async list(folder: string) {
    try {
      return (await readdir(folder, { withFileTypes: true })).filter(
        (entry) => !hidden(entry.name),
      );
    } catch {
      return null;
    }
  }

  problem(path: string, message: string) {
    this.problems.push({ path: relative(this.root, path).split(sep).join('/'), message });
  }
}

/**
 * The issues to report. Where a value matches none of a union's options, the issues of the option
 * it comes closest to, the one with the fewest, say more than that it matched none.
 */
function issuesOf(issues: readonly z.core.$ZodIssue[]): z.core.$ZodIssue[] {
  return issues.flatMap((issue) => {
    if (issue.code !== 'invalid_union' || issue.errors.length === 0) return [issue];
    const closest = issue.errors.reduce((best, each) => (each.length < best.length ? each : best));
    return issuesOf(closest.map((inner) => ({ ...inner, path: [...issue.path, ...inner.path] })));
  });
}

/** A name starting with a dot, such as a tool's cache or a system's own file. */
function hidden(name: string): boolean {
  return name.startsWith('.');
}

/** The courses in the folder of courses: each folder in it that isn't hidden. */
export async function courseSlugs(root: string): Promise<string[]> {
  return (await readdir(root, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory() && !hidden(entry.name))
    .map((entry) => entry.name)
    .sort();
}

function hash(files: Record<string, string>): string {
  const digest = createHash('sha256');
  for (const name of Object.keys(files).sort()) digest.update(`${name}\0${files[name]}\0`);
  return digest.digest('hex').slice(0, 16);
}

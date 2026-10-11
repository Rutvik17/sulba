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
  type CourseFile,
  courseFile,
  type LabFile,
  labFile,
  type ModuleFile,
  moduleFile,
  type StageFile,
  stageFile,
} from './schema.ts';

export interface Problem {
  /** The file or folder, from the folder of courses. */
  readonly path: string;
  readonly message: string;
}

export interface Stage extends StageFile {
  readonly slug: string;
  readonly brief: string;
  /** In the order they open. */
  readonly hints: readonly string[];
  readonly explanation: string;
  /** The code this stage starts from: a new file, or code added to the learner's own. */
  readonly starter: string;
  /** The learner's file as it should be once the stage is done. */
  readonly solution: string;
  /** Each test file, by its name in `tests/`. */
  readonly tests: Readonly<Record<string, string>>;
  /** The stage's figures.py, which computes the numbers its prose shows, if it has one. */
  readonly figures: string | null;
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

const prose = ['brief.md', 'hints.md', 'explanation.md'];

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
      if (stage) stages.push(stage);
    }
    return { ...file, slug, data, stages };
  }

  async stage(folder: string, slug: string): Promise<Stage | null> {
    const file = await this.yaml(join(folder, 'stage.yaml'), stageFile);
    await this.entries(
      folder,
      ['stage.yaml', ...prose],
      ['starter', 'solution', 'tests'],
      ['figures.py'],
    );
    if (!file) return null;
    await this.entries(join(folder, 'starter'), [file.file], []);
    await this.entries(join(folder, 'solution'), [file.file], []);
    const testNames = (await this.files(join(folder, 'tests'))).sort();
    for (const name of testNames) {
      if (!/^test_[a-z0-9_]+\.py$/.test(name)) {
        this.problem(join(folder, 'tests', name), 'A test file is named test_<name>.py.');
      }
    }
    if (testNames.length === 0) this.problem(join(folder, 'tests'), 'A stage needs a test file.');

    const [brief, hints, explanation, starter, solution] = await Promise.all([
      this.prose(join(folder, 'brief.md')),
      this.prose(join(folder, 'hints.md')),
      this.prose(join(folder, 'explanation.md')),
      this.text(join(folder, 'starter', file.file)),
      this.text(join(folder, 'solution', file.file)),
    ]);
    const tests: Record<string, string> = {};
    for (const name of testNames) {
      const text = await this.text(join(folder, 'tests', name));
      if (text !== null) tests[name] = text;
    }
    const figures = (await this.list(folder))?.some((entry) => entry.name === 'figures.py')
      ? await this.text(join(folder, 'figures.py'))
      : null;
    if (brief === null || hints === null || explanation === null) return null;
    if (starter === null || solution === null) return null;
    const hintList = hints.split(/^---$/m).map((hint) => hint.trim());
    if (hintList.some((hint) => hint === '')) {
      this.problem(join(folder, 'hints.md'), 'Each hint, between lines of ---, needs text.');
    }
    const version = hash({
      'stage.yaml': JSON.stringify(file),
      brief,
      hints,
      explanation,
      starter,
      solution,
      ...(figures === null ? {} : { 'figures.py': figures }),
      ...tests,
    });
    return {
      ...file,
      slug,
      brief,
      hints: hintList,
      explanation,
      starter,
      solution,
      tests,
      figures,
      version,
    };
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
    for (const issue of result.error.issues) {
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

  async list(folder: string) {
    try {
      return await readdir(folder, { withFileTypes: true });
    } catch {
      return null;
    }
  }

  problem(path: string, message: string) {
    this.problems.push({ path: relative(this.root, path).split(sep).join('/'), message });
  }
}

function hash(files: Record<string, string>): string {
  const digest = createHash('sha256');
  for (const name of Object.keys(files).sort()) digest.update(`${name}\0${files[name]}\0`);
  return digest.digest('hex').slice(0, 16);
}

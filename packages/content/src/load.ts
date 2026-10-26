// Reads a course folder into a typed tree. Every problem found is collected, so one check reports
// them all: a file that breaks its schema, a folder that is listed but missing or present but
// unlisted, a file a stage doesn't use, or prose with a tag Sulba doesn't support.
import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';
import { join, relative, sep } from 'node:path';
import Markdoc from '@markdoc/markdoc';
import { machinePackages } from '@sulba/lab/protocol';
import { parse } from 'yaml';
import type { z } from 'zod';
import {
  type Card,
  type CatchProblem,
  type ChartFile,
  type CourseFile,
  cardsFile,
  courseFile,
  type LabFile,
  labFile,
  type ModuleFile,
  moduleFile,
  type RubricPoint,
  type ShipCheck,
  type StageFile,
  stageFile,
} from './schema.ts';

export interface Problem {
  /** The file or folder, from the folder of courses. */
  readonly path: string;
  readonly message: string;
}

/** The files every lab project holds (decision record 25). */
const projectFiles = ['README.md', 'pyproject.toml', 'uv.lock'];

/**
 * The files a lab project holds for TypeScript stages, which every run has beside the learner's
 * files: the packages Node runs the tests with, and tsc's settings (decision record 39).
 */
export const nodeProjectFiles = ['package.json', 'package-lock.json', 'tsconfig.json'];

/**
 * The file a lab project holds for Go stages, which every run has beside the learner's files:
 * the module the tests import the learner's package from, and its Go version (decision record
 * 43).
 */
export const goProjectFiles = ['go.mod'];

/** A test file's name in Python, TypeScript, Go and Java. */
const testFileNames = [
  /^test_[a-z0-9_]+\.py$/,
  /^[a-z0-9_]+\.test\.ts$/,
  /^[a-z0-9]+_test\.go$/,
  /^[A-Z][A-Za-z0-9]*Test\.java$/,
];

export type { Card, CatchProblem, ChartFile, RubricPoint, ShipCheck } from './schema.ts';

/** A stage's chart: what stage.yaml says of it, and chart.py, which draws it. */
export interface Chart extends ChartFile {
  readonly code: string;
}

/** A stage that writes code, whose file, packages and chart a Design stage doesn't have. */
type CodeStageFile = Exclude<StageFile, { kind: 'design' }>;

export interface Stage
  extends Omit<StageFile, 'problems' | 'checks' | 'chart' | 'questions' | 'rubric' | 'pass'> {
  /** The file the learner works in. A Design stage writes no code, so its file is ''. */
  readonly file: string;
  readonly packages: CodeStageFile['packages'];
  /** A Catch stage's problems, in the order its review lists them. Other stages have none. */
  readonly problems: readonly CatchProblem[];
  /** A Ship stage's checks before it ships, in the order they show. Other stages have none. */
  readonly shipChecks: readonly ShipCheck[];
  /** A Design stage's follow-up questions, in Markdoc, in order. Other stages have none. */
  readonly questions: readonly string[];
  /** The points a Design stage's design is marked against. Other stages have none. */
  readonly rubric: readonly RubricPoint[];
  /** How many of its rubric's points a Design stage's design must meet to pass, or 0. */
  readonly pass: number;
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
  /** The review cards that come back for spaced review once the stage is passed. */
  readonly cards: readonly Card[];
  /** A hash of every file in the stage but its cards, so progress can tell when it has changed. */
  readonly version: string;
}

export type Dataset = LabFile['data'][number] & { readonly text: string };

/** A library's recorded results, which a lab's tests read at `references/<file>`. */
export interface Reference {
  readonly file: string;
  readonly text: string;
}

/** A file the lab gives its learner to build on, by its name in `given/` and in a run. */
export interface Given {
  readonly file: string;
  readonly text: string;
}

export interface Lab extends Omit<LabFile, 'stages' | 'data' | 'references' | 'given'> {
  readonly slug: string;
  readonly data: readonly Dataset[];
  readonly references: readonly Reference[];
  readonly given: readonly Given[];
  /**
   * The files a download of the lab puts beside the learner's (decision record 25), each by its
   * name in `project/`, or none when the lab has no project.
   */
  readonly project: Readonly<Record<string, string>>;
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
    const hasReferences = (file?.references.length ?? 0) > 0;
    const hasGiven = (file?.given.length ?? 0) > 0;
    const hasProject = (await this.folders(folder)).includes('project');
    await this.entries(
      folder,
      ['lab.yaml'],
      [
        ...(hasData ? ['data'] : []),
        ...(hasReferences ? ['references'] : []),
        ...(hasGiven ? ['given'] : []),
        'stages',
        ...(hasProject ? ['project'] : []),
      ],
    );
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
      const path = join(folder, 'data', set.file);
      const text = await this.text(path);
      if (text === null) continue;
      if (set.file.endsWith('.json')) {
        try {
          JSON.parse(text);
        } catch (error) {
          this.problem(path, `Not valid JSON: ${(error as Error).message}`);
          continue;
        }
      }
      data.push({ ...set, text });
    }
    const references = hasReferences
      ? await this.references(join(folder, 'references'), file.references)
      : [];
    const given = hasGiven ? await this.given(join(folder, 'given'), file.given) : [];
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
      // An interview problem is solved from nothing, so it starts from a file of its own.
      if (stage.kind === 'problem' && stages.some((earlier) => earlier.file === stage.file)) {
        this.problem(
          join(folder, 'stages', name, 'stage.yaml'),
          `file: A Problem stage starts from a file of its own, so no earlier stage may make ${stage.file}.`,
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
    const project = hasProject ? await this.project(join(folder, 'project')) : {};
    // A download puts the learner's files beside the project's, so they can't share a name.
    for (const stage of stages.filter((each) => Object.hasOwn(project, each.file))) {
      this.problem(
        join(folder, 'stages', stage.slug, 'stage.yaml'),
        `file: ${stage.file} is a file of the lab's project, so the learner's file needs another name.`,
      );
    }
    // A run and a download put the given files beside the learner's, so they can't share a name.
    for (const stage of stages.filter((each) => file.given.includes(each.file))) {
      this.problem(
        join(folder, 'stages', stage.slug, 'stage.yaml'),
        `file: ${stage.file} is a file the lab gives, so the learner's file needs another name.`,
      );
    }
    for (const name of file.given.filter((each) => Object.hasOwn(project, each))) {
      this.problem(
        join(folder, 'lab.yaml'),
        `given: ${name} is a file of the lab's project, so the given file needs another name.`,
      );
    }
    // A download carries the runner as sulba.py, and figures run as figures.py beside the lab's
    // files.
    for (const name of file.given.filter((each) => ['sulba.py', 'figures.py'].includes(each))) {
      this.problem(
        join(folder, 'lab.yaml'),
        `given: ${name} is a name the runner takes, so the given file needs another name.`,
      );
    }
    if (file.runs === 'machine') this.machineLab(folder, stages, hasProject);
    else this.browserLab(folder, file, stages);
    if (usesTypeScript(stages, file.given)) this.typeScriptLab(folder, file, project, hasProject);
    if (usesGo(stages, file.given)) this.goLab(folder, file, project, hasProject);
    if (usesJava(stages, file.given)) this.javaLab(folder, file, stages);
    if (file.runs !== 'machine' && stages.some((stage) => stage.file === 'Dockerfile')) {
      this.problem(
        join(folder, 'lab.yaml'),
        "runs: a Dockerfile stage runs on the learner's machine: set runs: machine.",
      );
    }
    this.fetchedNamed(join(folder, 'lab.yaml'), file);
    return { ...file, slug, data, references, given, project, stages };
  }

  /**
   * Each file a lab fetches has a name of its own in `data/`, where its datasets are too. Windows
   * and macOS take two names that differ only in case as one.
   */
  fetchedNamed(path: string, file: LabFile) {
    const taken = new Set(file.data.map((set) => set.file.toLowerCase()));
    file.fetch.forEach((source, index) => {
      source.files.forEach(({ file: name }, at) => {
        if (taken.has(name.toLowerCase())) {
          this.problem(
            path,
            `fetch.${index}.files.${at}.file: data/ already has a file named ${name}.`,
          );
        }
        taken.add(name.toLowerCase());
      });
    });
  }

  /**
   * A lab that runs on the learner's machine runs from its project (decision record 28), and its
   * stages need nothing a browser draws or times: a chart is drawn in the page, and a Problem or
   * Design stage's clock runs there. Its download carries the runner as sulba.py, so no learner's file
   * may take that name.
   */
  machineLab(folder: string, stages: readonly Stage[], hasProject: boolean) {
    if (!hasProject) {
      this.problem(
        join(folder, 'project'),
        "Missing: a lab that runs on the learner's machine runs from its project.",
      );
    }
    for (const stage of stages) {
      const path = join(folder, 'stages', stage.slug, 'stage.yaml');
      if (stage.kind === 'problem' || stage.kind === 'design') {
        const name = stage.kind === 'problem' ? 'Problem' : 'Design';
        this.problem(
          path,
          `kind: A ${name} stage's clock runs in the browser, so a lab that runs on the learner's machine can't have one.`,
        );
      }
      if (stage.chart) {
        this.problem(
          path,
          "chart: A chart is drawn in the browser, so a lab that runs on the learner's machine can't have one.",
        );
      }
      if (stage.file === 'sulba.py') {
        this.problem(
          path,
          "file: sulba.py is the runner a machine lab's download carries, so the learner's file needs another name.",
        );
      }
    }
  }

  /**
   * TypeScript runs in Node on the learner's machine, with the packages and settings the lab's
   * project gives (decision record 39).
   */
  typeScriptLab(
    folder: string,
    file: LabFile,
    project: Readonly<Record<string, string>>,
    hasProject: boolean,
  ) {
    if (file.runs !== 'machine') {
      this.problem(
        join(folder, 'lab.yaml'),
        "runs: TypeScript runs in Node on the learner's machine: set runs: machine.",
      );
    } else if (hasProject) {
      for (const name of nodeProjectFiles.filter((each) => !Object.hasOwn(project, each))) {
        this.problem(
          join(folder, 'project', name),
          `Missing: a lab's TypeScript runs with its project's ${name}.`,
        );
      }
    }
  }

  /**
   * Go runs on the learner's machine, with the module the lab's project gives (decision record
   * 43).
   */
  goLab(
    folder: string,
    file: LabFile,
    project: Readonly<Record<string, string>>,
    hasProject: boolean,
  ) {
    if (file.runs !== 'machine') {
      this.problem(
        join(folder, 'lab.yaml'),
        "runs: Go runs on the learner's machine: set runs: machine.",
      );
    } else if (hasProject) {
      for (const name of goProjectFiles.filter((each) => !Object.hasOwn(project, each))) {
        this.problem(
          join(folder, 'project', name),
          `Missing: a lab's Go runs with its project's ${name}.`,
        );
      }
    }
  }

  /**
   * Java runs on the learner's machine, and every class of a run shares Java's unnamed package
   * (decision record 45), so no two of a lab's test files, or a test file and a class the learner or
   * the lab writes, may name the same class.
   */
  javaLab(folder: string, file: LabFile, stages: readonly Stage[]) {
    if (file.runs !== 'machine') {
      this.problem(
        join(folder, 'lab.yaml'),
        "runs: Java runs on the learner's machine: set runs: machine.",
      );
    }
    const classes = new Map<string, string>();
    for (const name of [...file.given, ...stages.map((stage) => stage.file)]) {
      if (name.endsWith('.java')) classes.set(name, name);
    }
    for (const stage of stages) {
      for (const [kind, files] of [
        ['tests', stage.tests],
        ['checks', stage.checks],
      ] as const) {
        for (const name of Object.keys(files).filter((each) => each.endsWith('.java'))) {
          const at = join('stages', stage.slug, kind, name);
          const before = classes.get(name);
          if (before === undefined) classes.set(name, at);
          else
            this.problem(
              join(folder, at),
              `${name} is already a class of the lab's, in ${before}: a Java test file needs a name of its own.`,
            );
        }
      }
    }
  }

  /**
   * A lab that runs in the browser loads only packages Pyodide ships, and fetches no files: the site
   * serves its data.
   */
  browserLab(folder: string, file: LabFile, stages: readonly Stage[]) {
    if (file.given.length > 0) {
      this.problem(
        join(folder, 'lab.yaml'),
        "given: Only a lab that runs on the learner's machine gives files (decision record 37): set runs: machine.",
      );
    }
    if (file.fetch.length > 0) {
      this.problem(
        join(folder, 'lab.yaml'),
        "fetch: Only a lab that runs on the learner's machine fetches files: set runs: machine, or serve the data as a dataset.",
      );
    }
    if (file.models.length > 0) {
      this.problem(
        join(folder, 'lab.yaml'),
        "models: Only a lab that runs on the learner's machine serves models there: set runs: machine.",
      );
    }
    for (const stage of stages) {
      for (const name of stage.packages.filter(isMachinePackage)) {
        this.problem(
          join(folder, 'stages', stage.slug, 'stage.yaml'),
          `packages: Pyodide has no ${name}, so a lab whose stages load it runs on the learner's machine: set runs: machine in lab.yaml.`,
        );
      }
    }
  }

  /** A lab's recorded references, each JSON, and the make.py that records them. */
  async references(folder: string, files: readonly string[]): Promise<Reference[]> {
    await this.entries(folder, [...files, 'make.py'], []);
    const references: Reference[] = [];
    for (const name of files) {
      const path = join(folder, name);
      const text = await this.text(path);
      if (text === null) continue;
      try {
        JSON.parse(text);
      } catch (error) {
        this.problem(path, `Not valid JSON: ${(error as Error).message}`);
        continue;
      }
      references.push({ file: name, text });
    }
    return references;
  }

  /** The files a lab gives its learner, each the Python file lab.yaml names. */
  async given(folder: string, files: readonly string[]): Promise<Given[]> {
    await this.entries(folder, files, []);
    const given: Given[] = [];
    for (const name of files) {
      const text = await this.text(join(folder, name));
      if (text !== null) given.push({ file: name, text });
    }
    return given;
  }

  /**
   * A lab's project: its pyproject.toml, uv.lock and README.md, a conftest.py if it has one, and
   * for TypeScript, its package.json, package-lock.json and tsconfig.json, with a
   * tsconfig.build.json for what `uv run sulba.py build` compiles for the browser, and for Go, its
   * go.mod.
   */
  async project(folder: string): Promise<Record<string, string>> {
    const optional = ['conftest.py', ...nodeProjectFiles, 'tsconfig.build.json', ...goProjectFiles];
    await this.entries(folder, projectFiles, [], optional);
    const present = await this.files(folder);
    const project: Record<string, string> = {};
    for (const name of [...projectFiles, ...optional].filter((each) => present.includes(each))) {
      const text = await this.text(join(folder, name));
      if (text !== null) project[name] = text;
    }
    return project;
  }

  async stage(folder: string, slug: string): Promise<Stage | null> {
    const file = await this.yaml(join(folder, 'stage.yaml'), stageFile);
    // A Design stage whose stage.yaml breaks its schema is still held to a Design stage's files.
    if (file?.kind === 'design' || (!file && (await saysDesign(join(folder, 'stage.yaml'))))) {
      return this.designStage(folder, slug, file?.kind === 'design' ? file : null);
    }
    const hasChecks = file?.kind === 'catch' || file?.kind === 'ship';
    await this.entries(
      folder,
      ['stage.yaml', 'brief.md', 'explanation.md'],
      ['starter', 'solution', 'tests', ...(hasChecks ? ['checks'] : [])],
      ['hints.md', 'figures.py', 'chart.py', 'cards.yaml'],
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
    const cards = present.has('cards.yaml') ? await this.cards(join(folder, 'cards.yaml')) : [];
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
      questions: [],
      rubric: [],
      pass: 0,
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
      cards,
      version,
    };
  }

  /**
   * A Design stage (decision record 42): a brief, follow-up questions and a rubric, with no code, so
   * no starter, solution or tests.
   */
  async designStage(
    folder: string,
    slug: string,
    file: Extract<StageFile, { kind: 'design' }> | null,
  ): Promise<Stage | null> {
    await this.entries(
      folder,
      ['stage.yaml', 'brief.md', 'explanation.md'],
      [],
      ['hints.md', 'figures.py', 'cards.yaml'],
    );
    if (!file) return null;
    const present = new Set(((await this.list(folder)) ?? []).map((entry) => entry.name));
    const hasHints = present.has('hints.md');
    const [brief, hints, explanation] = await Promise.all([
      this.prose(join(folder, 'brief.md')),
      hasHints ? this.prose(join(folder, 'hints.md')) : Promise.resolve(''),
      this.prose(join(folder, 'explanation.md')),
    ]);
    const figures = present.has('figures.py') ? await this.text(join(folder, 'figures.py')) : null;
    const cards = present.has('cards.yaml') ? await this.cards(join(folder, 'cards.yaml')) : [];
    if (brief === null || hints === null || explanation === null) return null;
    const hintList = hasHints ? hints.split(/^---$/m).map((hint) => hint.trim()) : [];
    if (hintList.some((hint) => hint === '')) {
      this.problem(join(folder, 'hints.md'), 'Each hint, between lines of ---, needs text.');
    }
    if (/^---$/m.test(explanation)) {
      this.problem(
        join(folder, 'explanation.md'),
        "Only a Catch stage's explanation has a line of ---, where its problems go.",
      );
    }
    const path = join(folder, 'stage.yaml');
    for (const [index, question] of file.questions.entries()) {
      this.yamlProse(path, `questions.${index}`, question);
    }
    for (const [index, point] of file.rubric.entries()) {
      for (const field of ['point', 'answer'] as const)
        this.yamlProse(path, `rubric.${index}.${field}`, point[field]);
    }
    const version = hash({
      'stage.yaml': JSON.stringify(file),
      brief,
      hints,
      explanation,
      ...(figures === null ? {} : { 'figures.py': figures }),
    });
    return {
      ...file,
      file: '',
      packages: [],
      problems: [],
      shipChecks: [],
      slug,
      brief,
      hints: hintList,
      explanation: explanation.trim(),
      afterProblems: null,
      starter: '',
      solution: '',
      tests: {},
      checks: {},
      figures,
      chart: null,
      cards,
      version,
    };
  }

  /**
   * A stage's review cards. They stay out of the stage's version: a card can change without the
   * stage changing.
   */
  async cards(path: string): Promise<Card[]> {
    const file = await this.yaml(path, cardsFile);
    file?.cards.forEach((card, index) => {
      for (const side of ['front', 'back'] as const) {
        this.yamlProse(path, `cards.${index}.${side}`, card[side]);
      }
    });
    return file?.cards ?? [];
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

  /**
   * The test files in a folder, each by name: test_<name>.py, <name>.test.ts, <name>_test.go or
   * <Name>Test.java.
   */
  async testFiles(folder: string, none: string): Promise<Record<string, string>> {
    const names = (await this.files(folder)).sort();
    for (const name of names) {
      if (!testFileNames.some((form) => form.test(name))) {
        this.problem(
          join(folder, name),
          'A test file is named test_<name>.py, <name>.test.ts in TypeScript, <name>_test.go in Go, or <Name>Test.java in Java.',
        );
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
    const found = checkIds(checks);
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

/** Whether a stage.yaml that broke its schema says it's a Design stage. */
async function saysDesign(path: string): Promise<boolean> {
  try {
    const parsed: unknown = parse(await readFile(path, 'utf8'));
    return typeof parsed === 'object' && parsed !== null && 'kind' in parsed
      ? parsed.kind === 'design'
      : false;
  } catch {
    return false;
  }
}

/** Whether a stage writes code: every kind but a Design stage (decision record 42). */
export function writesCode(stage: Pick<Stage, 'kind'>): boolean {
  return stage.kind !== 'design';
}

/** A package that only the learner's machine runs, since Pyodide has no build of it. */
function isMachinePackage(name: string): boolean {
  return (machinePackages as readonly string[]).includes(name);
}

/** Whether any of a lab's stages, or any file it gives, is TypeScript. */
function usesTypeScript(stages: readonly Stage[], given: readonly string[]): boolean {
  return [
    ...given,
    ...stages.flatMap((stage) => [
      stage.file,
      ...Object.keys(stage.tests),
      ...Object.keys(stage.checks),
    ]),
  ].some((name) => name.endsWith('.ts'));
}

/** Whether any of a lab's stages, or any file it gives, is Go. */
function usesGo(stages: readonly Stage[], given: readonly string[]): boolean {
  return [
    ...given,
    ...stages.flatMap((stage) => [
      stage.file,
      ...Object.keys(stage.tests),
      ...Object.keys(stage.checks),
    ]),
  ].some((name) => name.endsWith('.go'));
}

/** Whether any of a lab's stages, or any file it gives, is Java. */
function usesJava(stages: readonly Stage[], given: readonly string[]): boolean {
  return [
    ...given,
    ...stages.flatMap((stage) => [
      stage.file,
      ...Object.keys(stage.tests),
      ...Object.keys(stage.checks),
    ]),
  ].some((name) => name.endsWith('.java'));
}

/**
 * The id of each test in a test file: in Python, its `@pytest.mark.id("tst_...")`, in TypeScript,
 * the start of its name, as in `test('tst_... Finds the user', ...)`, in Go, the start of its
 * subtest's name, as in `t.Run("tst_... Waits for a token", ...)`, and in Java, the start of its
 * display name, as in `@DisplayName("tst_... Refuses a blank id")`.
 */
export function testIds(name: string, text: string): string[] {
  const mark = name.endsWith('.ts')
    ? /\b(?:test|it)\(\s*['"`](tst_[0-9a-z]{6}) /g
    : name.endsWith('.go')
      ? /\bt\.Run\(\s*"(tst_[0-9a-z]{6}) /g
      : name.endsWith('.java')
        ? /@DisplayName\(\s*"(tst_[0-9a-z]{6}) /g
        : /@pytest\.mark\.id\(\s*["'](tst_[0-9a-z]{6})["']\s*\)/g;
  return [...text.matchAll(mark)].map((found) => found[1] as string);
}

/** The id of each check in a stage's check files, and the file it's in. */
export function checkIds(checks: Readonly<Record<string, string>>): Map<string, string> {
  const found = new Map<string, string>();
  for (const [name, text] of Object.entries(checks)) {
    for (const id of testIds(name, text)) found.set(id, name);
  }
  return found;
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

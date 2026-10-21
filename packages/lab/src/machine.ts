// What a machine lab's download tells its runner, sulba.py (decision record 28): the lab's stages
// in `.sulba/lab.json`, with each stage's tests and checks, the stage the download starts at, the
// lab's datasets, the files the runner fetches from their publishers (decision record 29), and the
// models `uv run sulba.py model` serves (decision record 34).
// Test files and a Catch stage's fixed code are in base64, so a look through the folder doesn't
// show them; they are there to be found, as they are in the page.
import type { FetchedFile } from './protocol.ts';

/** Where the download keeps what only the runner reads. */
export const runnerFolder = '.sulba';

/** One check a Catch or Ship stage's code must pass, as the runner prints it. */
export interface MachineCheck {
  /** The check's test id, such as tst_abc123. */
  readonly id: string;
  /** A Catch stage's problem, or a Ship stage's check, in plain text. */
  readonly title: string;
  /** What a Ship stage's check requires, and what it says when the code fails it. Empty otherwise. */
  readonly requires: string;
  readonly failure: string;
}

export interface MachineStage {
  readonly id: string;
  readonly version: string;
  /** The stage's name in its page's address, `?stage=<slug>`. */
  readonly slug: string;
  readonly title: string;
  readonly kind: 'build' | 'catch' | 'ship';
  /** The file the learner works in. */
  readonly file: string;
  /** The code the stage starts from: a new file, or code added to the learner's own. */
  readonly starter: string;
  /** Each test file in base64, by its path in a run, a Catch or Ship stage's checks among them. */
  readonly tests: Readonly<Record<string, string>>;
  readonly checks: readonly MachineCheck[];
  /** A Catch stage's code with every problem fixed, in base64, or null for other stages. */
  readonly fixed: string | null;
}

/** A file the runner fetches into the download's `data/` before the first run. */
export interface MachineFetch extends FetchedFile {
  /** Its name in `data/`. */
  readonly file: string;
}

/**
 * What a model does, which sets how llama.cpp's server runs it: a chat model answers a
 * conversation, an embedding model turns text into a vector, and a reranker scores passages for a
 * query.
 */
export const modelKinds = ['chat', 'embedding', 'reranking'] as const;

/**
 * A model the runner serves with llama.cpp's server: its name, which a request gives to reach it,
 * its kind, its GGUF file's pin, and for a chat model whose lab sets one, the tokens of
 * conversation it reads, in place of 4,096 (decision record 36).
 */
export interface MachineModel extends FetchedFile {
  readonly title: string;
  readonly kind: (typeof modelKinds)[number];
  readonly context?: number;
}

export interface MachineLab {
  readonly format: 1;
  readonly id: string;
  readonly title: string;
  /** The lab's page, which the runner's links lead to. */
  readonly page: string;
  /** The stage the download starts at, counting from 0. */
  readonly start: number;
  /**
   * The lab's datasets, by their path in the download and in a run, such as `data/votes.csv`: the
   * only files in `data/` a run reads as text.
   */
  readonly data: readonly string[];
  readonly fetch: readonly MachineFetch[];
  /** The models `uv run sulba.py model` serves, each by its title. */
  readonly models: readonly MachineModel[];
  readonly stages: readonly MachineStage[];
}

/** Text as base64 of its UTF-8, as Python's base64 module reads it. */
export function toBase64(text: string): string {
  let binary = '';
  for (const byte of new TextEncoder().encode(text)) binary += String.fromCharCode(byte);
  return btoa(binary);
}

/** A stage as lab.json holds it, from the stage's text, its test files and its checks. */
export function machineStage(
  stage: Omit<MachineStage, 'tests' | 'fixed'> & {
    readonly tests: Readonly<Record<string, string>>;
    readonly fixed: string | null;
  },
): MachineStage {
  return {
    ...stage,
    tests: Object.fromEntries(
      Object.entries(stage.tests).map(([path, text]) => [path, toBase64(text)]),
    ),
    fixed: stage.fixed === null ? null : toBase64(stage.fixed),
  };
}

/** lab.json's text. */
export function labJson(lab: Omit<MachineLab, 'format'>): string {
  const file: MachineLab = { format: 1, ...lab };
  return `${JSON.stringify(file, null, 2)}\n`;
}

/**
 * The files of a machine lab's download, each by its path in the download's folder: the lab's
 * project with the runner, its data, the learner's files as its first stage opens them, and in
 * the runner's folder, lab.json and the lab's references, which only the tests read.
 */
export function machineDownload(parts: {
  /** The project's files, the runner's among them (node.ts's `runnerFiles`). */
  readonly project: Readonly<Record<string, string>>;
  /** The lab's datasets and references, by their paths in a run, such as `data/votes.csv`. */
  readonly data: Readonly<Record<string, string>>;
  readonly files: Readonly<Record<string, string>>;
  readonly lab: Omit<MachineLab, 'format'>;
}): Record<string, string> {
  const download: Record<string, string> = { ...parts.project };
  for (const [path, text] of Object.entries(parts.data)) {
    download[path.startsWith('references/') ? `${runnerFolder}/${path}` : path] = text;
  }
  Object.assign(download, parts.files);
  download[`${runnerFolder}/lab.json`] = labJson(parts.lab);
  return download;
}

// The YAML files that give a course its structure. Folders are named by their address in the
// URL; the order of modules, labs and stages comes from these files, and ids from neither.
import { pythonPackages } from '@sulba/lab/protocol';
import { z } from 'zod';
import { type IdKind, idPattern } from './ids.ts';

const id = (kind: IdKind) =>
  z.string().regex(idPattern(kind), `Expected a ${kind} id such as ${idPattern(kind).source}`);

/** A folder's name, which is also its address in the URL. */
export const slug = z.string().regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, 'Expected lowercase-with-dashes');

const title = z.string().trim().min(1);

export const courseFile = z.strictObject({
  id: id('course'),
  title,
  levels: z
    .array(
      z.strictObject({
        id: id('level'),
        slug,
        title,
        modules: z.array(slug),
      }),
    )
    .min(1),
});

export const moduleFile = z.strictObject({
  id: id('module'),
  title,
  labs: z.array(slug),
});

/** A dataset a lab uses, with the credit its licence asks for. */
const dataset = z.strictObject({
  file: z.string().regex(/^[a-z0-9-]+\.csv$/),
  title,
  creators: z.array(title).min(1),
  url: z.url({ protocol: /^https$/ }),
  licence: z.strictObject({ name: title, url: z.url({ protocol: /^https$/ }) }),
  /** What Sulba changed, such as a split or recoded labels. */
  changes: title,
});

export const labFile = z.strictObject({
  id: id('lab'),
  title,
  /** What the learner builds, in a sentence or two, under the lab's title. */
  summary: title,
  data: z.array(dataset).default([]),
  stages: z.array(slug).min(1),
});

const stageFields = {
  id: id('stage'),
  title,
  /** What the stage builds on, a line of Markdoc above its brief. */
  builds: title,
  /** The file the learner works in. A later stage on the same file adds to their code. */
  file: z.string().regex(/^[a-z_][a-z0-9_]*\.py$/),
  packages: z.array(z.enum(pythonPackages)).default([]),
  /** About how long the stage takes. */
  minutes: z.int().positive(),
};

/** One problem in a Catch stage's code, found by one hidden check. */
const problem = z.strictObject({
  /** The id of the check in `checks/` that finds it. */
  check: id('test'),
  title,
  /** What the problem would cost, in Markdoc. */
  cost: title,
  /** How to fix it, in Markdoc. */
  fix: title,
  /** The smallest change to the starter that fixes this problem and no other. */
  edit: z.strictObject({ replace: z.string().min(1), with: z.string() }),
});

/** One check a Ship stage's code must pass before it ships. Its text is Markdoc. */
const shipCheck = z.strictObject({
  /** The id of the check in `checks/`. */
  check: id('test'),
  title,
  /** What the check requires of the code. */
  requires: title,
  /** What the learner reads when the code fails it. */
  failure: title,
});

/**
 * Build: the learner writes the core by hand. Catch: the learner reviews an assistant's code that
 * passes its own tests, and hidden checks find its problems. Ship: the learner's code passes
 * hidden tests, then the checks it must pass before it ships.
 */
export const stageFile = z.discriminatedUnion('kind', [
  z.strictObject({ ...stageFields, kind: z.literal('build') }),
  z.strictObject({ ...stageFields, kind: z.literal('catch'), problems: z.array(problem).min(1) }),
  z.strictObject({ ...stageFields, kind: z.literal('ship'), checks: z.array(shipCheck).min(1) }),
]);

export type CourseFile = z.infer<typeof courseFile>;
export type ModuleFile = z.infer<typeof moduleFile>;
export type LabFile = z.infer<typeof labFile>;
export type StageFile = z.infer<typeof stageFile>;
export type CatchProblem = z.infer<typeof problem>;
export type ShipCheck = z.infer<typeof shipCheck>;

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

export const stageFile = z.strictObject({
  id: id('stage'),
  /** Build: the learner writes the core by hand. Catch and Ship arrive with their first stages. */
  kind: z.enum(['build']),
  title,
  /** The file the learner works in. A later stage on the same file adds to their code. */
  file: z.string().regex(/^[a-z_][a-z0-9_]*\.py$/),
  packages: z.array(z.enum(pythonPackages)).default([]),
  /** About how long the stage takes. */
  minutes: z.int().positive(),
});

export type CourseFile = z.infer<typeof courseFile>;
export type ModuleFile = z.infer<typeof moduleFile>;
export type LabFile = z.infer<typeof labFile>;
export type StageFile = z.infer<typeof stageFile>;

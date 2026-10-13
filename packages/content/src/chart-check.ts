// Checks every stage's chart by drawing it with the stage's solution, in every runtime, at its
// sliders' first values and at both ends of each slider: chart.py draws without an error and gives
// a drawing the page can draw. At the first values, every runtime draws the same. Elsewhere they
// may not: training that never settles turns the runtimes' last-digit differences into visible
// ones.
import {
  type ChartRequest,
  type ChartResult,
  type Drawing,
  lineStyles,
  type RunRequest,
} from '@sulba/lab/protocol';
import { z } from 'zod';
import type { Chart, Course, Lab, Problem } from './load.ts';

/** Draws charts in one runtime and returns what each drew, in the same order. */
export type ChartRunner = (requests: readonly ChartRequest[]) => Promise<readonly ChartResult[]>;

const text = z.string().trim().min(1);

const axis = z
  .strictObject({ min: z.number(), max: z.number(), step: z.number().positive(), label: text })
  .refine(({ min, max }) => min < max, { message: 'max must be more than min.', path: ['max'] })
  .refine(({ min, max, step }) => (max - min) / step <= 20, {
    message: 'An axis has at most 20 steps between its ticks.',
    path: ['step'],
  });

const line = z
  .strictObject({
    style: z.enum(lineStyles),
    label: text,
    x: z.array(z.number()),
    y: z.array(z.number().nullable()),
  })
  .refine(({ x, y }) => x.length === y.length, {
    message: 'x and y must be as long as each other.',
  });

/** What chart() must return, with every number finite or null where it may be missing. */
const drawing = z.strictObject({
  x: axis,
  y: axis,
  lines: z.array(line).min(1),
  points: z.array(z.strictObject({ x: z.number(), y: z.number().nullable() })),
  readouts: z.array(z.strictObject({ label: text, value: text })),
  description: text,
});

/** What a stage's chart draws with in the checks: the lab's data and each stage's solution to it. */
export function chartFiles(lab: Lab, index: number, chart: Chart): RunRequest['files'] {
  const files: Record<string, string> = {};
  for (const set of lab.data) files[`data/${set.file}`] = set.text;
  for (const stage of lab.stages.slice(0, index + 1)) files[stage.file] = stage.solution;
  return { ...files, 'chart.py': chart.code };
}

/**
 * The values a chart is checked at: every slider at its first value, then each slider at each
 * end of its range, with the others at their first values.
 */
export function chartValues(chart: Chart): Record<string, number>[] {
  const first = Object.fromEntries(chart.sliders.map(({ name, value }) => [name, value]));
  const tried = [first];
  for (const slider of chart.sliders) {
    const ends =
      'stops' in slider ? [slider.stops[0], slider.stops.at(-1)] : [slider.min, slider.max];
    for (const end of ends) {
      if (end !== undefined && end !== slider.value) tried.push({ ...first, [slider.name]: end });
    }
  }
  return tried;
}

interface Case {
  readonly path: string;
  readonly request: ChartRequest;
  /** Whether the sliders are at their first values, where every runtime must draw the same. */
  readonly first: boolean;
}

function casesOf(courses: readonly Course[]): Case[] {
  return courses.flatMap((course) =>
    course.levels.flatMap((level) =>
      level.modules.flatMap((module) =>
        module.labs.flatMap((lab) =>
          lab.stages.flatMap((stage, index) => {
            const { chart } = stage;
            if (!chart) return [];
            const path = `${course.slug}/modules/${module.slug}/labs/${lab.slug}/stages/${stage.slug}`;
            const files = chartFiles(lab, index, chart);
            const packages = [
              ...new Set(lab.stages.slice(0, index + 1).flatMap((each) => each.packages)),
            ];
            return chartValues(chart).map((values, at) => ({
              path,
              request: { files, values, packages },
              first: at === 0,
            }));
          }),
        ),
      ),
    ),
  );
}

/** Values as a sentence shows them, such as "w = 1, b = 0". */
function said(values: Readonly<Record<string, number>>): string {
  const pairs = Object.entries(values).map(([name, value]) => `${name} = ${value}`);
  return pairs.length ? `with ${pairs.join(', ')}` : 'with no sliders';
}

/** Where two drawings first differ, such as `readouts.0.value`, or null if they agree. */
function difference(a: unknown, b: unknown, at = ''): string | null {
  if (typeof a === 'number' && typeof b === 'number') {
    return Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a), Math.abs(b)) ? null : at;
  }
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return at;
    for (const [index, item] of a.entries()) {
      const found = difference(item, b[index], at ? `${at}.${index}` : String(index));
      if (found !== null) return found;
    }
    return null;
  }
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) {
      const found = difference(
        (a as Record<string, unknown>)[key],
        (b as Record<string, unknown>)[key],
        at ? `${at}.${key}` : key,
      );
      if (found !== null) return found;
    }
    return null;
  }
  return a === b ? null : at;
}

/** The part of a drawing at a path such as `readouts.0.value`. */
function partOf(value: unknown, path: string): unknown {
  return path
    .split('.')
    .filter(Boolean)
    .reduce<unknown>((part, key) => (part as Record<string, unknown> | undefined)?.[key], value);
}

/** Every problem with every stage's chart. */
export async function checkCharts(
  courses: readonly Course[],
  runners: Readonly<Record<string, ChartRunner>>,
): Promise<Problem[]> {
  const cases = casesOf(courses);
  if (cases.length === 0) return [];
  const requests = cases.map(({ request }) => request);
  const results = await Promise.all(
    Object.entries(runners).map(async ([name, run]) => [name, await run(requests)] as const),
  );
  const problems: Problem[] = [];
  cases.forEach(({ path, request, first: compared }, index) => {
    const file = `${path}/chart.py`;
    const values = said(request.values);
    const drawn: [runtime: string, drawing: Drawing][] = [];
    for (const [runtime, all] of results) {
      const result = all[index];
      if (!result) continue;
      if (result.problem) {
        const { kind, message } = result.problem;
        problems.push({ path: file, message: `${runtime}, ${values}: ${kind}: ${message}` });
        continue;
      }
      const parsed = drawing.safeParse(result.chart);
      if (!parsed.success) {
        for (const issue of parsed.error.issues) {
          const at = issue.path.length ? `${issue.path.join('.')}: ` : '';
          problems.push({ path: file, message: `${runtime}, ${values}: ${at}${issue.message}` });
        }
        continue;
      }
      drawn.push([runtime, parsed.data]);
    }
    const [first, ...rest] = drawn;
    if (!first) return;
    const [runtime, picture] = first;
    for (const [other, its] of compared ? rest : []) {
      const at = difference(its, picture);
      if (at !== null) {
        problems.push({
          path: file,
          message: `${values}, ${other} draws ${at} as ${JSON.stringify(partOf(its, at))}, but ${runtime} draws ${JSON.stringify(partOf(picture, at))}.`,
        });
      }
    }
  });
  return problems;
}

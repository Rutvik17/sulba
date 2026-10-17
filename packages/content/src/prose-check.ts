// Checks a course's prose once each stage's figures.py has run: the figures come out the same in
// every runtime, every formula renders, every figure the prose names exists and every figure is
// shown, and the math font has a glyph for every character a formula draws. A stage's prose
// includes its review cards, a Catch stage's what each problem costs and its fix, and a Ship
// stage's the text of each check.
import type { Figures, RunRequest } from '@sulba/lab/protocol';
import { drawnCharacters } from './glyphs.ts';
import type { Course, Lab, Problem, Stage } from './load.ts';
import { renderProse } from './prose.ts';
import { labFiles } from './runs.ts';

/** Computes figures for sets of files in one runtime, in the same order. */
export type FiguresRunner = (
  fileSets: readonly RunRequest['files'][],
) => Promise<readonly Figures[]>;

interface PlacedStage {
  readonly path: string;
  readonly lab: Lab;
  readonly stage: Stage;
}

function stagesWithPaths(courses: readonly Course[], only?: ReadonlySet<string>): PlacedStage[] {
  return courses.flatMap((course) =>
    course.levels.flatMap((level) =>
      level.modules.flatMap((module) =>
        module.labs.flatMap((lab) =>
          lab.stages
            .filter((stage) => only?.has(stage.id) ?? true)
            .map((stage) => ({
              path: `${course.slug}/modules/${module.slug}/labs/${lab.slug}/stages/${stage.slug}`,
              lab,
              stage,
            })),
        ),
      ),
    ),
  );
}

/** What figures.py runs with: the lab's data and references beside it. */
export function figuresFiles(lab: Lab, stage: Stage): RunRequest['files'] {
  return { ...labFiles(lab), 'figures.py': stage.figures ?? '' };
}

/**
 * Each stage's figures, by stage id, from every runtime: they must agree. With `only`, just the
 * stages with those ids.
 */
export async function computeFigures(
  courses: readonly Course[],
  runners: Readonly<Record<string, FiguresRunner>>,
  only?: ReadonlySet<string>,
): Promise<{ figures: Map<string, Record<string, string>>; problems: Problem[] }> {
  const stages = stagesWithPaths(courses, only).filter(({ stage }) => stage.figures !== null);
  const fileSets = stages.map(({ lab, stage }) => figuresFiles(lab, stage));
  const results = await Promise.all(
    Object.entries(runners).map(async ([name, runner]) => [name, await runner(fileSets)] as const),
  );
  const figures = new Map<string, Record<string, string>>();
  const problems: Problem[] = [];
  stages.forEach(({ path, stage }, index) => {
    const answers = results.map(([name, all]) => [name, all[index]] as const);
    for (const [name, answer] of answers) {
      if (answer?.problem)
        problems.push({ path: `${path}/figures.py`, message: `${name}: ${answer.problem}` });
    }
    const [first, ...rest] = answers;
    if (!first?.[1]?.figures) return;
    for (const [name, answer] of rest) {
      if (answer?.figures && JSON.stringify(answer.figures) !== JSON.stringify(first[1].figures)) {
        problems.push({
          path: `${path}/figures.py`,
          message: `${name} gives ${JSON.stringify(answer.figures)}, but ${first[0]} gives ${JSON.stringify(first[1].figures)}.`,
        });
      }
    }
    figures.set(stage.id, { ...first[1].figures });
  });
  return { figures, problems };
}

function hex(point: number): string {
  return `U+${point.toString(16).toUpperCase().padStart(4, '0')}`;
}

/**
 * Problems in every stage's prose, or with `only`, the prose of the stages with those ids, given
 * their figures and the characters the math font has.
 */
export function proseProblems(
  courses: readonly Course[],
  figures: ReadonlyMap<string, Readonly<Record<string, string>>>,
  mathFont: ReadonlySet<number>,
  only?: ReadonlySet<string>,
): Problem[] {
  const problems: Problem[] = [];
  for (const { path, stage } of stagesWithPaths(courses, only)) {
    const values = figures.get(stage.id) ?? {};
    const used = new Set<string>();
    const pieces: [file: string, text: string, oneLine?: boolean][] = [
      ['brief.md', stage.brief],
      ['stage.yaml', stage.builds, true],
      ...stage.hints.map((hint): [string, string] => ['hints.md', hint]),
      ...[stage.explanation, stage.afterProblems]
        .filter((text) => text !== null)
        .map((text): [string, string] => ['explanation.md', text]),
      ...stage.problems.flatMap(({ cost, fix }): [string, string][] => [
        ['stage.yaml', cost],
        ['stage.yaml', fix],
      ]),
      ...stage.shipChecks.flatMap(({ title, requires, failure }) =>
        [title, requires, failure].map((text): [string, string, boolean] => [
          'stage.yaml',
          text,
          true,
        ]),
      ),
      ...stage.cards.flatMap(({ front, back }): [string, string][] => [
        ['cards.yaml', front],
        ['cards.yaml', back],
      ]),
    ];
    for (const [file, text, oneLine] of pieces) {
      const rendered = renderProse(text, values, { oneLine: oneLine ?? false });
      for (const message of rendered.errors) problems.push({ path: `${path}/${file}`, message });
      for (const name of rendered.used) used.add(name);
      const missing = new Set<number>();
      for (const formula of rendered.formulas) {
        for (const point of drawnCharacters(formula)) if (!mathFont.has(point)) missing.add(point);
      }
      for (const point of missing) {
        problems.push({
          path: `${path}/${file}`,
          message: `The math font has no ${String.fromCodePoint(point)} (${hex(point)}), so it would come from another font.`,
        });
      }
    }
    for (const name of Object.keys(values)) {
      if (!used.has(name)) {
        problems.push({ path: `${path}/figures.py`, message: `The prose never shows ${name}.` });
      }
    }
  }
  return problems;
}

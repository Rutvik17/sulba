// Checks a course's prose once each stage's figures.py has run: the figures come out the same in
// every runtime, every formula renders, every figure the prose names exists and every figure is
// shown, and the math font has a glyph for every character a formula draws. A Catch stage's prose
// includes what each problem costs and its fix.
import type { Figures, RunRequest } from '@sulba/lab/protocol';
import { drawnCharacters } from './glyphs.ts';
import type { Course, Lab, Problem, Stage } from './load.ts';
import { renderProse } from './prose.ts';

/** Computes figures for sets of files in one runtime, in the same order. */
export type FiguresRunner = (
  fileSets: readonly RunRequest['files'][],
) => Promise<readonly Figures[]>;

interface PlacedStage {
  readonly path: string;
  readonly lab: Lab;
  readonly stage: Stage;
}

function stagesWithPaths(courses: readonly Course[]): PlacedStage[] {
  return courses.flatMap((course) =>
    course.levels.flatMap((level) =>
      level.modules.flatMap((module) =>
        module.labs.flatMap((lab) =>
          lab.stages.map((stage) => ({
            path: `${course.slug}/modules/${module.slug}/labs/${lab.slug}/stages/${stage.slug}`,
            lab,
            stage,
          })),
        ),
      ),
    ),
  );
}

/** What figures.py runs with: the lab's data beside it. */
export function figuresFiles(lab: Lab, stage: Stage): RunRequest['files'] {
  const files: Record<string, string> = {};
  for (const set of lab.data) files[`data/${set.file}`] = set.text;
  return { ...files, 'figures.py': stage.figures ?? '' };
}

/** Each stage's figures, by stage id, from every runtime: they must agree. */
export async function computeFigures(
  courses: readonly Course[],
  runners: Readonly<Record<string, FiguresRunner>>,
): Promise<{ figures: Map<string, Record<string, string>>; problems: Problem[] }> {
  const stages = stagesWithPaths(courses).filter(({ stage }) => stage.figures !== null);
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

/** Problems in every stage's prose, given its figures and the characters the math font has. */
export function proseProblems(
  courses: readonly Course[],
  figures: ReadonlyMap<string, Readonly<Record<string, string>>>,
  mathFont: ReadonlySet<number>,
): Problem[] {
  const problems: Problem[] = [];
  for (const { path, stage } of stagesWithPaths(courses)) {
    const values = figures.get(stage.id) ?? {};
    const used = new Set<string>();
    const pieces: [file: string, text: string][] = [
      ['brief.md', stage.brief],
      ...stage.hints.map((hint) => ['hints.md', hint] as [string, string]),
      ['explanation.md', stage.explanation],
      ...stage.problems.flatMap(({ cost, fix }) => [
        ['stage.yaml', cost] as [string, string],
        ['stage.yaml', fix] as [string, string],
      ]),
    ];
    for (const [file, text] of pieces) {
      const rendered = renderProse(text, values);
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

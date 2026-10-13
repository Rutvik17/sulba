import { fileURLToPath } from 'node:url';
import { pyodideEngine } from '@sulba/lab/node';
import { beforeAll, expect, test } from 'vitest';
import { type Course, loadCourse } from './load.ts';
import { mathFontCharacters } from './math-font.ts';
import { computeFigures, type FiguresRunner, proseProblems } from './prose-check.ts';

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const count = 'demo/modules/counting/labs/tallies/stages/count';
let course: Course;
let pyodide: FiguresRunner;

beforeAll(async () => {
  const loaded = await loadCourse(fixtures, 'demo');
  if (!loaded.course) throw new Error(JSON.stringify(loaded.problems));
  course = loaded.course;
  const engine = await pyodideEngine();
  pyodide = async (fileSets) => fileSets.map(engine.figures);
}, 120_000);

const countStage = () => course.levels[0]?.modules[0]?.labs[0]?.stages[0];

/** The fixture course with one stage's explanation, or figures, replaced. */
function changed(change: { explanation?: string; figures?: string }): Course {
  const [level] = course.levels;
  const [module] = level?.modules ?? [];
  const [lab] = module?.labs ?? [];
  if (!level || !module || !lab) throw new Error('The fixture course has no lab.');
  const [first, ...rest] = lab.stages;
  if (!first) throw new Error('The fixture lab has no stage.');
  const stages = [{ ...first, ...change }, ...rest];
  return {
    ...course,
    levels: [{ ...level, modules: [{ ...module, labs: [{ ...lab, stages }] }] }],
  };
}

test("the fixture course's figures and prose have no problems", async () => {
  const { figures, problems } = await computeFigures([course], { Pyodide: pyodide });
  expect(problems).toEqual([]);
  expect(figures.get(countStage()?.id ?? '')).toEqual({ total: '3', yes: '2' });
  expect(proseProblems([course], figures, mathFontCharacters())).toEqual([]);
});

test('figures that differ between runtimes are a problem', async () => {
  // The count stage's figures differ; every other stage's agree.
  const other: FiguresRunner = async (fileSets) =>
    (await pyodide(fileSets)).map((answer) =>
      answer.figures?.total ? { figures: { ...answer.figures, yes: '1' }, problem: null } : answer,
    );
  const { problems } = await computeFigures([course], { Pyodide: pyodide, Other: other });
  expect(problems).toEqual([
    {
      path: `${count}/figures.py`,
      message: 'Other gives {"total":"3","yes":"1"}, but Pyodide gives {"total":"3","yes":"2"}.',
    },
  ]);
});

test('a figure the prose never shows is a problem', async () => {
  const { figures } = await computeFigures([course], { Pyodide: pyodide });
  const course2 = changed({ explanation: 'The poll has {% $fig.total %} votes.\n' });
  expect(proseProblems([course2], figures, mathFontCharacters())).toEqual([
    { path: `${count}/figures.py`, message: 'The prose never shows yes.' },
  ]);
});

test('a character the math font lacks is a problem', async () => {
  const { figures } = await computeFigures([course], { Pyodide: pyodide });
  const font = mathFontCharacters();
  font.delete(0x2211);
  expect(proseProblems([course], figures, font)).toEqual([
    {
      path: `${count}/explanation.md`,
      message: 'The math font has no ∑ (U+2211), so it would come from another font.',
    },
  ]);
});

test("a formula in a Catch problem's prose is checked like the rest", async () => {
  const { figures } = await computeFigures([course], { Pyodide: pyodide });
  const [level] = course.levels;
  const [module] = level?.modules ?? [];
  const [lab] = module?.labs ?? [];
  const catchStage = lab?.stages[2];
  if (!level || !module || !lab || !catchStage)
    throw new Error('The fixture lab has no Catch stage.');
  const problems = catchStage.problems.map((problem, index) =>
    index === 0 ? { ...problem, cost: 'The order is `$\\sqrt{2$`.' } : problem,
  );
  const stages = lab.stages.map((stage) => (stage === catchStage ? { ...stage, problems } : stage));
  const broken: Course = {
    ...course,
    levels: [{ ...level, modules: [{ ...module, labs: [{ ...lab, stages }] }] }],
  };
  expect(proseProblems([broken], figures, mathFontCharacters())).toEqual([
    {
      path: 'demo/modules/counting/labs/tallies/stages/check/stage.yaml',
      message: expect.stringMatching(/^The formula \\sqrt\{2 doesn't render: /),
    },
  ]);
});

test("a Ship check's text shows figures, and is one line, checked like the rest", async () => {
  const { figures } = await computeFigures([course], { Pyodide: pyodide });
  const [level] = course.levels;
  const [module] = level?.modules ?? [];
  const [lab] = module?.labs ?? [];
  const shipStage = lab?.stages[3];
  if (!level || !module || !lab || !shipStage)
    throw new Error('The fixture lab has no Ship stage.');
  const [fast, rest] = shipStage.shipChecks;
  if (!fast || !rest) throw new Error('The fixture Ship stage has no checks.');
  const shipChecks = [
    { ...fast, title: 'Fast on {% $fig.most %} votes' },
    { ...rest, requires: 'It leaves the list.\n\nIt returns a choice.' },
  ];
  const stages = lab.stages.map((stage) =>
    stage === shipStage ? { ...stage, shipChecks } : stage,
  );
  const broken: Course = {
    ...course,
    levels: [{ ...level, modules: [{ ...module, labs: [{ ...lab, stages }] }] }],
  };
  const path = 'demo/modules/counting/labs/tallies/stages/ship';
  expect(proseProblems([broken], figures, mathFontCharacters())).toEqual([
    { path: `${path}/stage.yaml`, message: "Undefined variable: 'fig.most'" },
    { path: `${path}/stage.yaml`, message: 'This text is one line, alone.' },
  ]);
});

test('a formula that doesn’t render is a problem', async () => {
  const { figures } = await computeFigures([course], { Pyodide: pyodide });
  const broken = changed({
    explanation: '{% $fig.total %} {% $fig.yes %}\n\n```math\n\\sqrt{2\n```\n',
  });
  expect(proseProblems([broken], figures, mathFontCharacters())).toEqual([
    {
      path: `${count}/explanation.md`,
      message: expect.stringMatching(/^The formula \\sqrt\{2 doesn't render: /),
    },
  ]);
});

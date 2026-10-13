import { fileURLToPath } from 'node:url';
import { pyodideEngine } from '@sulba/lab/node';
import { beforeAll, expect, test } from 'vitest';
import { type ChartRunner, chartValues, checkCharts } from './chart-check.ts';
import { type Chart, type Course, loadCourse } from './load.ts';

const fixtures = fileURLToPath(new URL('../fixtures/courses/', import.meta.url));
const share = 'demo/modules/counting/labs/tallies/stages/share';
let course: Course;
let pyodide: ChartRunner;

beforeAll(async () => {
  const loaded = await loadCourse(fixtures, 'demo');
  if (!loaded.course) throw new Error(JSON.stringify(loaded.problems));
  course = loaded.course;
  const engine = await pyodideEngine();
  pyodide = async (requests) => requests.map(engine.chart);
}, 120_000);

function shareChart(): Chart {
  const chart = course.levels[0]?.modules[0]?.labs[0]?.stages[1]?.chart;
  if (!chart) throw new Error('The fixture lab has no chart.');
  return chart;
}

/** The fixture course with the share stage's chart changed. */
function changed(change: Partial<Chart>): Course {
  const [level] = course.levels;
  const [module] = level?.modules ?? [];
  const [lab] = module?.labs ?? [];
  if (!level || !module || !lab) throw new Error('The fixture course has no lab.');
  const stages = lab.stages.map((stage) =>
    stage.chart ? { ...stage, chart: { ...stage.chart, ...change } } : stage,
  );
  return {
    ...course,
    levels: [{ ...level, modules: [{ ...module, labs: [{ ...lab, stages }] }] }],
  };
}

test("the fixture course's chart draws without a problem", async () => {
  expect(await checkCharts([course], { Pyodide: pyodide })).toEqual([]);
});

test("a chart is checked at each slider's first value, then at each end of each slider", () => {
  const chart: Chart = {
    ...shareChart(),
    sliders: [
      { name: 'w', label: 'Weight', min: 0, max: 2, step: 0.5, value: 1 },
      { name: 'lr', label: 'Learning rate', stops: [0.1, 1, 10], value: 10 },
    ],
  };
  expect(chartValues(chart)).toEqual([
    { w: 1, lr: 10 },
    { w: 0, lr: 10 },
    { w: 2, lr: 10 },
    { w: 1, lr: 0.1 },
  ]);
});

test('a chart.py that raises an error is a problem', async () => {
  const code = 'def chart(votes):\n    return 1 / votes / 0\n';
  expect(await checkCharts([changed({ code })], { Pyodide: pyodide })).toEqual([
    {
      path: `${share}/chart.py`,
      message: 'Pyodide, with votes = 3: ZeroDivisionError: division by zero',
    },
    {
      path: `${share}/chart.py`,
      message: 'Pyodide, with votes = 1: ZeroDivisionError: division by zero',
    },
  ]);
});

test('a drawing the page cannot draw is a problem', async () => {
  const code = shareChart().code.replace('"step": 0.5', '"step": 0.01');
  expect(await checkCharts([changed({ code })], { Pyodide: pyodide })).toContainEqual({
    path: `${share}/chart.py`,
    message: 'Pyodide, with votes = 3: y.step: An axis has at most 20 steps between its ticks.',
  });
});

test('a line without a label for the legend is a problem', async () => {
  const code = shareChart().code.replace(`"label": "Your share", `, '');
  expect(await checkCharts([changed({ code })], { Pyodide: pyodide })).toContainEqual({
    path: `${share}/chart.py`,
    message:
      'Pyodide, with votes = 3: lines.1.label: Invalid input: expected string, received undefined',
  });
});

test("drawings that differ between runtimes are a problem at the sliders' first values", async () => {
  const other: ChartRunner = async (requests) =>
    (await pyodide(requests)).map((result) =>
      result.chart
        ? { ...result, chart: { ...result.chart, readouts: [{ label: 'share', value: '1' }] } }
        : result,
    );
  const problems = await checkCharts([course], { Pyodide: pyodide, Other: other });
  expect(problems).toContainEqual({
    path: `${share}/chart.py`,
    message:
      'with votes = 3, Other draws readouts.0.label as "share", but Pyodide draws "Share of yes in the first 3".',
  });
});

test('drawings may differ between runtimes away from the first values', async () => {
  // Only the drawing with one vote counted differs.
  const other: ChartRunner = async (requests) =>
    (await pyodide(requests)).map((result, index) =>
      requests[index]?.values.votes === 1 && result.chart
        ? { ...result, chart: { ...result.chart, description: 'Another' } }
        : result,
    );
  expect(await checkCharts([course], { Pyodide: pyodide, Other: other })).toEqual([]);
});

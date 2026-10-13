# 16. Draw charts in SVG, from the data a stage's chart.py returns

- Status: accepted
- Date: 2026-10-13

## Context

The logistic regression lab's first three stages each end with a chart of the learner's own functions, redrawn as a slider moves: the sigmoid as its weight and bias change, the loss along one weight with the slope the gradient gives, and training at a chosen learning rate. Every chart a learner sees must come from code that runs in CI (CLAUDE.md). Learners' code runs in Pyodide in a Web Worker (decision record 5). The interface takes every colour from the design tokens, in a dark and a light theme (decision record 11), and a screen reader must be able to read the page.

## Decision

- **Drawing:** a stage's `chart.py` defines `chart()`, which imports the learner's functions, takes each slider's value by its name, and returns plain data: two axes, lines in one of four styles with a label each for the legend, marked points, the values to read beside the chart, and a description for screen readers (`courses/README.md`).
- **Running:** the lab's worker runs it as it runs tests, under the same time limit, and only the latest values wait while a chart is drawn.
- **Showing:** the workspace's Chart tab draws the data in SVG, with a React component in `packages/ui` whose lines take their colours from the tokens. Until the stage is passed, it shows the solution's drawing, faded.
- **Describing:** `stage.yaml` gives the chart's title and sliders.
- **Checks:** `pnpm check:content` draws every chart with the stage's solution, at its sliders' first values and at each end of each slider, in Pyodide and in CPython.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| SVG, drawn by a React component from chart.py's data (chosen) | No new dependency; colours follow the theme without a redraw; text is real text, at the page's sizes; the data costs about 1 ms a draw | Each kind of mark is Sulba's to build: lines and points for now |
| Matplotlib in Pyodide, shown as an image | Draws any kind of chart | 10.17 MB more to download, 4.4 s to import, 90 to 230 ms a redraw; fixed colours that can't follow the theme; letters drawn as paths |
| Chart.js 4.5.1 or uPlot 1.6.32, drawing chart.py's data on a canvas | Mature; uPlot is 23 KB gzipped for a line chart | A canvas can't take the tokens' colours without script reading them, and redrawing when the theme changes; a screen reader sees nothing without added ARIA |
| Observable Plot 0.6.17 or Recharts 3.10.1, drawing chart.py's data in SVG | SVG, so tokens and text work; Recharts adds keyboard navigation | 88 KB and 98 KB gzipped for a line chart, with d3, or Redux and d3, among their dependencies |

## Evidence

- Matplotlib 3.10.8 in Pyodide 314.0.7 needs nine wheels the lab doesn't already load, 10,172,530 bytes in all, per [`pyodide-lock.json`](https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide-lock.json) and the files beside it.
- Measured in Node with Pyodide 314.0.7, median of ten runs:
  - loading matplotlib took 1.08 s, and importing `matplotlib.pyplot` 4.39 s;
  - a redraw took 92 to 161 ms as SVG and 105 to 232 ms as PNG;
  - the same chart's data, as JSON, took 0.9 ms.
- Matplotlib's own `matplotlibrc` draws SVG text as paths (`svg.fonttype: path`), and it rejects `var(--line)` as a colour.
- Chart.js "renders chart elements on an HTML5 canvas", and "canvas rendering disallows CSS styling" ([Chart.js](https://www.chartjs.org/docs/latest/)). A canvas's content "will not be accessible to screen readers" without ARIA or fallback content ([Chart.js accessibility](https://www.chartjs.org/docs/latest/general/accessibility.html)).
- uPlot passes its colours straight to the canvas's `strokeStyle` and `fillStyle` ([uPlot docs](https://github.com/leeoniya/uPlot/blob/master/docs/README.md)). A canvas ignores a colour it can't parse ([HTML: fillStyle](https://html.spec.whatwg.org/multipage/canvas.html#dom-context-2d-fillstyle)), and in Chromium `var(--line)` left `fillStyle` unchanged. An SVG stroke of `var(--line)` followed a change to the token without a redraw.
- Gzipped, built with esbuild for a line chart alone: Chart.js 48.6 KB, uPlot 23.0 KB, Observable Plot 88.0 KB with d3, Recharts 98.3 KB. Their dependencies are listed on npm. Observable Plot's marks default to `currentColor` ([Plot](https://github.com/observablehq/plot/blob/main/docs/features/plots.md)). Recharts 3 adds "aria labels, roles, and keyboard controls" by default ([Recharts and accessibility](https://github.com/recharts/recharts/wiki/Recharts-and-accessibility)).

## Why

A lab's chart is a few lines and points, redrawn as a slider moves, in either theme. Drawn in SVG from data, it needs no new dependency, takes the tokens as they are, keeps its text as text and costs nothing to load. Matplotlib would draw anything, but it adds 10 MB and seconds before the first chart, and its pictures can't follow the theme. The canvas libraries are mature, but each needs script to read colours and ARIA to be read at all. The strongest case against the choice: each new kind of chart, such as bars or a histogram, is code Sulba writes, where a library would bring it.

## Consequences

A new kind of mark changes the drawing format, its check and the component. Every move of a slider runs Python: the training chart trains twice, which takes 0.3 to 0.5 seconds in Chromium. Away from the sliders' first values, Pyodide and CPython can draw differently where training never settles, so the check compares them only at the first values.

## Revisit when

A lab needs a kind of chart that would cost more to build than a library weighs, or charts have to be drawn outside a browser.

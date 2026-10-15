import type { Lab } from '@sulba/lab/client';
import type { ChartRequest, ChartResult } from '@sulba/lab/protocol';
import { Chart, decimalsOf, Legend } from '@sulba/ui/chart';
import { classes } from '@sulba/ui/classes';
import { Slider } from '@sulba/ui/slider';
import { type ReactNode, useEffect, useMemo, useRef, useState } from 'react';
import type { ChartView, LabView } from '../lib/labs';
import styles from './chart.module.css';
import { labData } from './data';
import { latestOnly } from './latest';
import { chartOf, previewOf } from './stages';
import { kept } from './storage';

const css = classes(styles, 'chart', 'sliders', 'readouts', 'problem');

/** Each slider's first value, by the name chart() takes it as. */
function firstValues(chart: ChartView): Record<string, number> {
  return Object.fromEntries(chart.sliders.map(({ name, value }) => [name, value]));
}

/** A drawing, and whether it is of the learner's code or the solution's preview. */
interface Drawn {
  readonly live: boolean;
  readonly result: ChartResult | 'failed';
}

interface Props {
  readonly lab: LabView;
  readonly index: number;
  readonly python: Lab | null;
  /** Until the stage is passed, the chart shows the solution's, faded, and its sliders are fixed. */
  readonly passed: boolean;
  /** The learner's code, as the editor has it. */
  readonly code: () => string;
  /** How many runs have finished: after each, the chart draws the code as it stands. */
  readonly runs: number;
}

/**
 * A stage's chart, drawn by its chart.py with the learner's code, its legend, its sliders and the
 * values to read.
 */
export function ChartPanel({ lab, index, python, passed, code, runs }: Props) {
  const chart = lab.stages[index]?.chart;
  if (!chart) throw new Error(`Stage ${index + 1} has no chart.`);
  const [values, setValues] = useState(() => firstValues(chart));
  const [drawn, setDrawn] = useState<Drawn | null>(null);
  const shown = useRef(true);

  useEffect(() => {
    shown.current = true;
    return () => {
      shown.current = false;
    };
  }, []);

  const draw = useMemo(
    () =>
      python &&
      latestOnly(
        ({ request }: { live: boolean; request: Promise<ChartRequest> }) =>
          request.then((ready) => python.chart(ready)).catch(() => 'failed' as const),
        ({ live }, result: Drawn['result']) => {
          if (shown.current) setDrawn({ live, result });
        },
      ),
    [python],
  );

  // biome-ignore lint/correctness/useExhaustiveDependencies: runs isn't read, but each run that finishes redraws the chart with the code as it stands.
  useEffect(() => {
    const now = passed ? code() : null;
    draw?.({
      live: passed,
      request: labData(lab).then((data) =>
        now === null
          ? previewOf(lab, data, index, firstValues(chart))
          : chartOf(lab, data, index, now, kept, values),
      ),
    });
  }, [draw, passed, values, runs, lab, index, chart, code]);

  // A drawing of the other kind, such as the preview just after the stage is passed, isn't shown.
  const result = drawn?.live === passed ? drawn.result : null;
  const picture = result === 'failed' ? null : result;
  const problem = picture?.problem ?? null;
  let notice: ReactNode = null;
  if (!passed) notice = 'Opens when your tests pass.';
  else if (result === 'failed')
    notice = 'Python didn’t load. Check your connection, then run the tests again.';
  else if (problem?.kind === 'TimeLimit') notice = 'Your code ran past the 5-second limit.';
  else if (problem) notice = 'Your code raised an error.';
  // The legend names each line, the one drawn on top first.
  const legend = [...(picture?.chart?.lines ?? [])]
    .reverse()
    .map(({ style, label }) => ({ line: style, label }));

  return (
    <div className={css.chart}>
      <Chart drawing={picture?.chart ?? null} faded={!passed} notice={notice} />
      {problem && problem.kind !== 'TimeLimit' && (
        <p className={css.problem}>
          {problem.message ? `${problem.kind}: ${problem.message}` : problem.kind}
        </p>
      )}
      {legend.length > 0 && <Legend items={legend} />}
      {chart.sliders.length > 0 && (
        <div className={css.sliders}>
          {chart.sliders.map((slider) => {
            const value = values[slider.name] ?? slider.value;
            const set = (next: number) =>
              setValues((before) => ({ ...before, [slider.name]: next }));
            if ('stops' in slider) {
              const { stops } = slider;
              return (
                <Slider
                  key={slider.name}
                  label={slider.label}
                  minValue={0}
                  maxValue={stops.length - 1}
                  value={stops.indexOf(value)}
                  valueText={(at) => String(stops[at])}
                  onChange={(at) => set(stops[at] ?? slider.value)}
                  isDisabled={!passed}
                />
              );
            }
            const decimals = decimalsOf(slider.step);
            return (
              <Slider
                key={slider.name}
                label={slider.label}
                minValue={slider.min}
                maxValue={slider.max}
                step={slider.step}
                value={value}
                formatOptions={{ minimumFractionDigits: decimals, maximumFractionDigits: decimals }}
                onChange={(next) => set(Number(next.toFixed(decimals)))}
                isDisabled={!passed}
              />
            );
          })}
        </div>
      )}
      {passed && picture?.chart && picture.chart.readouts.length > 0 && (
        <dl className={css.readouts} aria-live="polite">
          {picture.chart.readouts.map(({ label, value }, at) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: a chart's readouts keep their order.
            <div key={at}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

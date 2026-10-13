import { type ReactNode, useId, useLayoutEffect, useRef, useState } from 'react';
import { classes } from '../classes';
import styles from './chart.module.css';
import { type Axis, labelEvery, pathOf, ticksOf } from './plot';

export { type Axis, decimalsOf } from './plot';

const css = classes(
  styles,
  'chart',
  'faded',
  'grid',
  'tick',
  'name',
  'main',
  'base',
  'faint',
  'dashed',
  'point',
  'notice',
  'legend',
  'swatch',
);

/**
 * How a line is drawn. main: the learner's own result. base: a curve to read it against. faint: a
 * result to compare with. dashed: a level, such as the lowest loss there is.
 */
export type LineStyle = 'main' | 'base' | 'faint' | 'dashed';

export interface Drawing {
  readonly x: Axis;
  readonly y: Axis;
  /** In the order they are drawn, so a later line lies on top. A null y breaks its line. */
  readonly lines: readonly {
    readonly style: LineStyle;
    readonly x: readonly number[];
    readonly y: readonly (number | null)[];
  }[];
  /** Points marked on top, in the main style. */
  readonly points: readonly { readonly x: number; readonly y: number | null }[];
  /** What the chart shows, read in place of the picture. */
  readonly description: string;
}

export interface ChartProps {
  /** What to draw, or null for an empty plot, such as while it is drawn. */
  readonly drawing: Drawing | null;
  /**
   * Draws it faintly, such as a preview of what the learner's code will draw. A screen reader
   * skips a faded drawing and reads the notice.
   */
  readonly faded?: boolean;
  /** A short message over the plot, such as why it is faded. */
  readonly notice?: ReactNode;
}

/** The width of a character of a tick's label, and the room between a label and the plot. */
const CHAR = 6.7;
const GAP = 8;

/**
 * A line chart, drawn in SVG at its box's own size, 4:3, so its text stays at the page's sizes
 * on any screen. Its colours come from the theme.
 */
export function Chart({ drawing, faded = false, notice }: ChartProps) {
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(640);
  // An id fit for url(#…), whatever characters React's ids hold.
  const clip = `clip${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`;

  useLayoutEffect(() => {
    const element = box.current;
    if (!element) return;
    const measure = () => setWidth(element.getBoundingClientRect().width || 640);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={box} className={faded ? `${css.chart} ${css.faded}` : css.chart}>
      {drawing && (
        <Plot drawing={drawing} width={width} height={width * 0.75} clip={clip} hidden={faded} />
      )}
      {notice && (
        <div className={css.notice}>
          <p>{notice}</p>
        </div>
      )}
    </div>
  );
}

interface PlotProps {
  readonly drawing: Drawing;
  readonly width: number;
  readonly height: number;
  readonly clip: string;
  /** Hidden from screen readers. */
  readonly hidden: boolean;
}

function Plot({ drawing, width, height, clip, hidden }: PlotProps) {
  const { x, y } = drawing;
  const xTicks = ticksOf(x);
  const yTicks = ticksOf(y);
  const widest = (ticks: typeof xTicks) => Math.max(...ticks.map(({ label }) => label.length));
  const left = widest(yTicks) * CHAR + 2 * GAP;
  const right = GAP * 2;
  const top = GAP * 3;
  const bottom = GAP * 5;
  const across = width - left - right;
  const down = height - top - bottom;
  const toX = (value: number) => left + ((value - x.min) / (x.max - x.min)) * across;
  const toY = (value: number) => top + (1 - (value - y.min) / (y.max - y.min)) * down;
  const place = (a: number, b: number) => [toX(a), toY(b)] as const;
  const xEvery = labelEvery(across / (xTicks.length - 1), widest(xTicks) * CHAR + 2 * GAP);
  const yEvery = labelEvery(down / (yTicks.length - 1), 2 * GAP + 4);
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={drawing.description}
      aria-hidden={hidden || undefined}
    >
      <defs>
        <clipPath id={clip}>
          <rect x={left} y={top} width={across} height={down} />
        </clipPath>
      </defs>
      {yTicks.map(({ value, label }, index) => (
        <g key={value}>
          <line className={css.grid} x1={left} x2={width - right} y1={toY(value)} y2={toY(value)} />
          {index % yEvery === 0 && (
            <text className={css.tick} x={left - GAP} y={toY(value)} dy="0.32em" textAnchor="end">
              {label}
            </text>
          )}
        </g>
      ))}
      {xTicks.map(
        ({ value, label }, index) =>
          index % xEvery === 0 && (
            <text
              key={value}
              className={css.tick}
              x={toX(value)}
              y={top + down + GAP}
              dy="0.8em"
              textAnchor="middle"
            >
              {label}
            </text>
          ),
      )}
      <text className={css.name} x={left} y={top - GAP}>
        {y.label}
      </text>
      <text className={css.name} x={width - right} y={height - GAP} textAnchor="end">
        {x.label}
      </text>
      <g clipPath={`url(#${clip})`}>
        {drawing.lines.map((line, index) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: a chart's lines keep their order.
          <path key={index} className={css[line.style]} d={pathOf(line.x, line.y, place)} />
        ))}
        {drawing.points.map(
          (point, index) =>
            point.y !== null &&
            Number.isFinite(point.x) &&
            Number.isFinite(point.y) && (
              // biome-ignore lint/suspicious/noArrayIndexKey: a chart's points keep their order.
              <circle key={index} className={css.point} cx={toX(point.x)} cy={toY(point.y)} r={4} />
            ),
        )}
      </g>
    </svg>
  );
}

export interface LegendProps {
  /** Each style of line a chart draws, and what it shows. */
  readonly items: readonly { readonly line: LineStyle; readonly label: ReactNode }[];
}

/** What each line in a chart shows, beside a stroke drawn as the chart draws it. */
export function Legend({ items }: LegendProps) {
  return (
    <ul className={css.legend}>
      {items.map(({ line, label }, at) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: a legend keeps its order.
        <li key={at}>
          <svg className={css.swatch} viewBox="0 0 16 8" aria-hidden="true">
            <line className={css[line]} x1="0" x2="16" y1="4" y2="4" />
          </svg>
          {label}
        </li>
      ))}
    </ul>
  );
}

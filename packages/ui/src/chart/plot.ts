// The geometry of a chart: where each tick goes and what it says, and each line as an SVG path.

/** An axis: the values it spans, the step between its labelled ticks, and what it measures. */
export interface Axis {
  readonly min: number;
  readonly max: number;
  readonly step: number;
  readonly label: string;
}

/** How many decimals a step has, such as 2 for 0.25: every tick is written with that many. */
export function decimalsOf(step: number): number {
  // In exponent form, so a step such as 1e-7 counts its decimals too.
  const [mantissa = '', exponent = '0'] = step.toExponential().split('e');
  const [, fraction = ''] = mantissa.split('.');
  return Math.max(0, fraction.length - Number(exponent));
}

/** Each tick on an axis, from its min to its max: its value and how it is written. */
export function ticksOf(axis: Axis): { readonly value: number; readonly label: string }[] {
  const decimals = decimalsOf(axis.step);
  const scale = 10 ** decimals;
  const count = Math.round((axis.max - axis.min) / axis.step);
  return Array.from({ length: count + 1 }, (_, index) => {
    // Rounded to the step's decimals, and + 0 turns -0 into 0, so no tick reads "-0.0".
    const value = Math.round((axis.min + index * axis.step) * scale) / scale + 0;
    return { value, label: value.toFixed(decimals) };
  });
}

/**
 * How many ticks apart labels go so that each has room: 1 labels every tick, 2 every other.
 * `spacing` is the distance between ticks and `room` the distance a label needs.
 */
export function labelEvery(spacing: number, room: number): number {
  return Math.max(1, Math.ceil(room / spacing));
}

/** Whether a value lies on an axis, its ends included. */
export function within(axis: Axis, value: number): boolean {
  return value >= axis.min && value <= axis.max;
}

/** Far enough outside any chart to stand for a value off it, near enough for SVG to draw. */
const FAR = 1e6;

/**
 * A line through the points as an SVG path. A point without a finite value breaks the line, so
 * each run of points between breaks is a separate stroke.
 */
export function pathOf(
  xs: readonly number[],
  ys: readonly (number | null)[],
  place: (x: number, y: number) => readonly [number, number],
): string {
  const parts: string[] = [];
  let drawing = false;
  xs.forEach((x, index) => {
    const y = ys[index];
    if (y === null || y === undefined || !Number.isFinite(x) || !Number.isFinite(y)) {
      drawing = false;
      return;
    }
    const [left, top] = place(x, y);
    parts.push(`${drawing ? 'L' : 'M'}${near(left)} ${near(top)}`);
    drawing = true;
  });
  return parts.join('');
}

/** A coordinate to a hundredth of a pixel, and no further off the chart than FAR. */
function near(at: number): number {
  return Math.round(Math.min(FAR, Math.max(-FAR, at)) * 100) / 100;
}

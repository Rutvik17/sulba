import { Chart, type Drawing, Legend } from '@sulba/ui/chart';

const xs = Array.from({ length: 161 }, (_, index) => -8 + index / 10);
const sigmoid = (x: number) => 1 / (1 + Math.exp(-x));

/** A sigmoid at w = 2, b = -1, against w = 1, b = 0, the way a lab's chart draws one. */
const drawing: Drawing = {
  x: { min: -8, max: 8, step: 2, label: 'x' },
  y: { min: 0, max: 1, step: 0.25, label: 'probability' },
  lines: [
    { style: 'faint', x: xs, y: xs.map(sigmoid) },
    { style: 'dashed', x: [-8, 8], y: [0.5, 0.5] },
    { style: 'base', x: [-8, 8], y: [0.1, 0.9] },
    { style: 'main', x: xs, y: xs.map((x) => sigmoid(2 * x - 1)) },
  ],
  // The second point sits on the axes' ends, where it shows whole.
  points: [
    { x: 0.5, y: 0.5 },
    { x: 8, y: 1 },
  ],
  description: 'A sigmoid with w = 2 and b = -1, crossing 0.5 at x = 0.50.',
};

const legend = [
  { line: 'main', label: 'Your sigmoid' },
  { line: 'base', label: 'A straight line' },
  { line: 'faint', label: 'w = 1, b = 0' },
  { line: 'dashed', label: '0.5' },
] as const;

/** A chart with every style of line, a faded preview under a notice, and an error with nothing drawn. */
export default function ChartDemo() {
  return (
    <>
      <figure>
        <Chart drawing={drawing} />
        <Legend items={legend} />
      </figure>
      <figure>
        <Chart drawing={drawing} faded notice="Opens when your tests pass." />
      </figure>
      <figure>
        <Chart drawing={null} notice="Your code raised an error." />
      </figure>
    </>
  );
}

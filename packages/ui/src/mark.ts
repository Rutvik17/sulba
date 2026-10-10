/*
  Sulba's mark: the cord. Śulba is Sanskrit for "cord". The Śulba Sūtras, India's oldest texts
  on geometry, laid out altars with pegs and a cord. A cord of twelve equal lengths stretched
  over three pegs into sides of 3, 4 and 5 makes a true right angle, because 3² + 4² = 5².

  Everything here is computed from the 3, 4 and 5, in a 100 × 100 box: the right angle at the
  bottom left, the side of 3 standing up from it and the side of 4 running right.
*/

type Point = readonly [x: number, y: number];

const UNIT = 21;
const LEFT = 50 - 2 * UNIT;
const BOTTOM = 50 + 1.5 * UNIT;

/** The three pegs: the top of the side of 3, the right angle, the end of the side of 4. */
export const pegs: readonly [top: Point, corner: Point, end: Point] = [
  [LEFT, BOTTOM - 3 * UNIT],
  [LEFT, BOTTOM],
  [LEFT + 4 * UNIT, BOTTOM],
];

/** The cord as SVG path data, from the top peg round the triangle. */
export const cordPath = `M${pegs.map(([x, y]) => `${x} ${y}`).join(' L')} Z`;

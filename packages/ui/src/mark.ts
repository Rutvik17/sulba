/*
  Sulba's mark: the cord. Śulba is Sanskrit for "cord". The Śulba Sūtras, among the oldest
  geometry that survives from India, laid out altars with poles and a cord. A cord of twelve equal
  lengths stretched over three pegs into sides of 3, 4 and 5 makes a true right angle, because
  3² + 4² = 5².

  Everything here is computed from the 3, 4 and 5, in a 100 × 100 box: the right angle at the
  bottom left, the side of 3 standing up from it and the side of 4 running right.
*/

type Point = readonly [x: number, y: number];

/** The sides, in lengths of cord: up from the right angle, across from it, and back. */
export const sides = [3, 4, 5] as const;

const [UP, ACROSS, BACK] = sides;
const UNIT = 21;
const LEFT = 50 - (ACROSS / 2) * UNIT;
const BOTTOM = 50 + (UP / 2) * UNIT;

const top: Point = [LEFT, BOTTOM - UP * UNIT];
const corner: Point = [LEFT, BOTTOM];
const end: Point = [LEFT + ACROSS * UNIT, BOTTOM];

/** The three pegs: the top of the side of 3, the right angle, the end of the side of 4. */
export const pegs: readonly [top: Point, corner: Point, end: Point] = [top, corner, end];

/** The cord as SVG path data, from the top peg round the triangle. */
export const cordPath = `M${pegs.map(([x, y]) => `${x} ${y}`).join(' L')} Z`;

/** The points between two pegs that split their side into equal lengths of cord. */
function between(from: Point, to: Point, lengths: number): Point[] {
  return Array.from({ length: lengths - 1 }, (_, i) => [
    from[0] + ((to[0] - from[0]) * (i + 1)) / lengths,
    from[1] + ((to[1] - from[1]) * (i + 1)) / lengths,
  ]);
}

/** Every peg and knot in order round the cord from the top peg, one length of cord apart. */
export const loop: readonly Point[] = [
  top,
  ...between(top, corner, UP),
  corner,
  ...between(corner, end, ACROSS),
  end,
  ...between(end, top, BACK),
];

/** The knots: the points on the loop that are not pegs. */
export const knots: readonly Point[] = loop.filter((point) => !pegs.includes(point));

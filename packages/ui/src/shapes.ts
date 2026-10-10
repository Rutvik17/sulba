/*
  The avatar shapes: twelve patterns of fixed geometry, each drawn in a 96 × 96 tile and seen
  through a round window. Each is SVG markup with no fill or stroke of its own: lines take the
  stroke they are drawn with, and a dot (class "dot") is a path of no length that a round cap
  turns into a dot. Coordinates are rounded to one decimal place.
*/

const S = 96;
const C = S / 2;

type Point = readonly [x: number, y: number];

const f = (v: number) => String(Number(v.toFixed(1)));
const poly = (points: readonly Point[]) =>
  `M${points.map(([x, y]) => `${f(x)} ${f(y)}`).join(' L')}`;
const circle = (cx: number, cy: number, r: number) =>
  `<circle cx="${f(cx)}" cy="${f(cy)}" r="${f(r)}"/>`;
const line = (x1: number, y1: number, x2: number, y2: number) =>
  `<line x1="${f(x1)}" y1="${f(y1)}" x2="${f(x2)}" y2="${f(y2)}"/>`;
const path = (d: string) => `<path d="${d}"/>`;
const range = (from: number, to: number, step = 1) =>
  Array.from({ length: Math.ceil((to - from) / step) }, (_, i) => from + i * step);

// Six waves, two periods across the tile, each drawn as joined parabolic arcs.
function waves() {
  return range(0, 6).map((k) => {
    const y = f(8 + k * 16);
    return path(
      `M-24 ${y}Q-12 ${f(8 + k * 16 - 10)} 0 ${y}T24 ${y}T48 ${y}T72 ${y}T96 ${y}T120 ${y}`,
    );
  });
}

// Parallel lines at 45 degrees, 13.6 apart.
function rain() {
  const step = 13.6 * Math.SQRT2;
  const lines: string[] = [];
  for (let c = -S; c <= S; c += step) lines.push(line(c - 8, -8, c + S + 8, S + 8));
  return lines;
}

// Concentric circles around a point near the lower left corner.
function ripple() {
  return range(14, 140, 14).map((r) => circle(14, 82, r));
}

// Twelve rays, long and short in turn, stopping well inside the edge so it reads as a sunburst, not
// a wheel.
function sun() {
  return range(0, 12).map((k) => {
    const a = (2 * Math.PI * k) / 12 - Math.PI / 2;
    const outer = k % 2 === 0 ? 40 : 28;
    return line(
      C + 13 * Math.cos(a),
      C + 13 * Math.sin(a),
      C + outer * Math.cos(a),
      C + outer * Math.sin(a),
    );
  });
}

// Half circles about two centres d apart, either side of the middle. Each half circle ends where
// the next one, one d wider, begins, so each half turn widens the spiral by d.
function spiral() {
  const d = 7.2;
  const left = C - d / 2;
  const right = C + d / 2;
  let r = 3.6;
  let out = `M${f(left + r)} ${f(C)}`;
  for (let k = 0; r < 70; k++, r += d) {
    const x = k % 2 === 0 ? left - r : right + r;
    out += `A${f(r)} ${f(r)} 0 0 1 ${f(x)} ${f(C)}`;
  }
  return [path(out)];
}

// A six by six grid of dots, as one path.
function dots() {
  const d = range(8, 96, 16)
    .flatMap((x) => range(8, 96, 16).map((y) => `M${x} ${y}h.01`))
    .join('');
  return [`<path class="dot" d="${d}"/>`];
}

// An isometric cube, each face hatched in its own direction.
function cube() {
  const r = 42;
  const w = r * Math.cos(Math.PI / 6);
  const top: Point = [C, C - r];
  const upperRight: Point = [C + w, C - r / 2];
  const lowerRight: Point = [C + w, C + r / 2];
  const bottom: Point = [C, C + r];
  const lowerLeft: Point = [C - w, C + r / 2];
  const upperLeft: Point = [C - w, C - r / 2];
  const middle: Point = [C, C];
  const at = (a: Point, b: Point, t: number): Point => [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
  ];
  const out = [
    path(`${poly([top, upperRight, lowerRight, bottom, lowerLeft, upperLeft, top])} Z`),
    path(poly([upperLeft, middle, upperRight])),
    path(poly([middle, bottom])),
  ];
  const n = 7;
  for (let k = 1; k < n; k++) {
    const t = k / n;
    // The top face's lines run parallel to its left edges, the left face's stand upright and the
    // right face's run parallel to its top edge.
    for (const [a, b] of [
      [at(upperLeft, top, t), at(middle, upperRight, t)],
      [at(upperLeft, middle, t), at(lowerLeft, bottom, t)],
      [at(middle, bottom, t), at(upperRight, lowerRight, t)],
    ] as const) {
      out.push(line(a[0], a[1], b[0], b[1]));
    }
  }
  return out;
}

// Nested half circles standing on a line.
function arch() {
  return [
    ...[10, 22, 34, 46, 58].map((r) =>
      path(`M${f(C - r)} 70 A${f(r)} ${f(r)} 0 0 1 ${f(C + r)} 70`),
    ),
    line(-4, 70, S + 4, 70),
  ];
}

// Nested chevrons, pointing up.
function peaks() {
  return range(0, 6).map((k) => {
    const y = 30 + k * 13;
    return path(
      poly([
        [-6, y + 40],
        [C, y],
        [S + 6, y + 40],
      ]),
    );
  });
}

// Ramer–Douglas–Peucker: keeps only the points that lie further than tol from the line between the
// points kept either side of them.
function simplify(points: readonly Point[], tol: number): readonly Point[] {
  const first = points[0];
  const last = points.at(-1);
  if (points.length < 3 || !first || !last) return points;
  const [dx, dy] = [last[0] - first[0], last[1] - first[1]];
  const norm = Math.hypot(dx, dy) || 1;
  let far = 0;
  let at = 0;
  points.forEach(([x, y], i) => {
    if (i === 0 || i === points.length - 1) return;
    const distance = Math.abs(dy * (x - first[0]) - dx * (y - first[1])) / norm;
    if (distance > far) [far, at] = [distance, i];
  });
  if (far <= tol) return [first, last];
  return [
    ...simplify(points.slice(0, at + 1), tol).slice(0, -1),
    ...simplify(points.slice(at), tol),
  ];
}

// Logistic curves of different steepness, all through the centre.
function sigmoid() {
  return [0.05, 0.08, 0.12, 0.18, 0.3, 0.6].map((steepness) => {
    const points = range(-16, 405).map((i): Point => {
      const x = i / 4;
      return [x, 76 - 56 / (1 + Math.exp(-steepness * (x - C)))];
    });
    return path(poly(simplify(points, 0.12)));
  });
}

// Upright lines whose heights follow a normal curve, on a base line.
function bell() {
  const bars = range(0, 13)
    .map((k) => {
      const x = 6 + k * 7;
      const height = 64 * Math.exp(-((x - C) ** 2) / (2 * 16 ** 2));
      return `M${f(x)} 82V${f(82 - Math.max(height, 2))}`;
    })
    .join('');
  return [path(`${bars}M-4 82H100`)];
}

// Parallel staircases.
function steps() {
  return range(-3, 4).map((k) =>
    path(`M${f(-8 + k * 16)} ${f(72 + k * 16)}${'v-16h16'.repeat(9)}`),
  );
}

const draw = {
  Waves: waves,
  Rain: rain,
  Ripple: ripple,
  Sun: sun,
  Spiral: spiral,
  Dots: dots,
  Cube: cube,
  Arch: arch,
  Peaks: peaks,
  Sigmoid: sigmoid,
  'Bell curve': bell,
  Steps: steps,
} as const;

export type ShapeName = keyof typeof draw;

/** Each shape's SVG markup, for a 96 × 96 viewBox. */
export const shapes = Object.fromEntries(
  Object.entries(draw).map(([name, shape]) => [name, shape().join('')]),
) as Record<ShapeName, string>;

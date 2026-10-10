/*
  Draws Sulba's pictures for its accounts on other sites into brand/, at the repository's root: the
  profile picture in both themes and the banners, each at the size its site asks for. Everything
  comes from the mark's geometry, the avatar shapes and the design tokens, and Chromium renders
  each picture one pixel to one pixel.

    pnpm brand
*/
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { chromium } from '@playwright/test';
import { knots, pegs } from '@sulba/ui/mark';
import { type ShapeName, shapes } from '@sulba/ui/shapes';

type Point = (typeof pegs)[number];

interface Theme {
  ground: string;
  tile: string;
  ink: string;
}

const require = createRequire(import.meta.url);
const out = path.resolve(import.meta.dirname, '../../../brand');

// The colours are the site's: the page, a raised surface and the text, in each theme.
const tokens = readFileSync(require.resolve('@sulba/ui/tokens.css'), 'utf8');
function theme(selector: string): Theme {
  const start = tokens.indexOf(selector);
  const block = tokens.slice(tokens.indexOf('{', start), tokens.indexOf('}', start));
  const value = (name: string) => {
    const found = block.match(new RegExp(`--${name}:\\s*([^;]+);`))?.[1];
    if (!found) throw new Error(`${selector} sets no --${name}`);
    return found.trim();
  };
  return { ground: value('bg'), tile: value('raise'), ink: value('fg') };
}
const themes = {
  dark: theme(':root[data-theme="dark"]'),
  light: theme(':root[data-theme="light"]'),
};

// The cord's three pegs lie on a circle whose diameter is its long side, so the circle's centre is
// the middle of that side. Pictures centre that circle.
const [top, , end] = pegs;
const centre: Point = [(top[0] + end[0]) / 2, (top[1] + end[1]) / 2];
const radius = Math.hypot(end[0] - top[0], end[1] - top[1]) / 2;

const n = (v: number) => Number(v.toFixed(2));

/*
  The profile picture as SVG, size × size. The circle through the pegs reaches REACH of the
  picture's half-width, well inside a round crop. Widths are shares of the picture: thin enough to
  read as the avatar shapes' hairlines, thick enough to show at 48 px. Under 200 px the knots would
  be specks, so they are left out.
*/
const REACH = 0.66;
const WEIGHT = { line: 0.0175, knot: 0.04, peg: 0.0775 };

function profile(size: number, { tile, ink }: Theme) {
  const k = (REACH * size) / 2 / radius;
  const at = ([x, y]: Point): Point => [
    n(size / 2 + (x - centre[0]) * k),
    n(size / 2 + (y - centre[1]) * k),
  ];
  const dot = (point: Point, width: number) => {
    const [x, y] = at(point);
    return `<circle cx="${x}" cy="${y}" r="${n((width * size) / 2)}" fill="${ink}"/>`;
  };
  const cord = pegs.map((peg) => at(peg).join(' ')).join(' L');
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" width="${size}" height="${size}">`,
    '<title>Sulba</title>',
    `<rect width="${size}" height="${size}" fill="${tile}"/>`,
    `<path d="M${cord} Z" fill="none" stroke="${ink}" stroke-width="${n(WEIGHT.line * size)}" stroke-linejoin="round"/>`,
    ...(size >= 200 ? knots.map((knot) => dot(knot, WEIGHT.knot)) : []),
    ...pegs.map((peg) => dot(peg, WEIGHT.peg)),
    '</svg>',
  ].join('\n');
}

/*
  A banner: a row of round windows onto the avatar shapes, the cord in the middle one, and the
  school's line under them. `scale` is how many of the picture's pixels make one pixel where the
  site shows it, so the lines and dots come out at the avatar shapes' 1.2 px and 3.5 px there.
*/
interface Banner {
  width: number;
  height: number;
  windows: readonly (ShapeName | 'cord')[];
  size: number;
  gap: number;
  row: number;
  line: { y: number; size: number };
  scale: number;
}

const serif = pathToFileURL(
  require.resolve('@fontsource/instrument-serif/files/instrument-serif-latin-400-normal.woff2'),
);

function banner(b: Banner, { ground, tile, ink }: Theme) {
  const share = 0.62;
  const s = (48 * share) / radius;
  const cord = `<g transform="translate(48 48) scale(${n(s)}) translate(${-centre[0]} ${-centre[1]})">
    <path d="M${pegs.map((p) => p.join(' ')).join(' L')} Z"/>
    <path class="dot" d="${knots.map(([x, y]) => `M${n(x)} ${n(y)}h0`).join('')}"/>
    <path class="peg" d="${pegs.map(([x, y]) => `M${x} ${y}h0`).join('')}"/>
  </g>`;
  const span = b.windows.length * b.size + (b.windows.length - 1) * b.gap;
  const windows = b.windows.map((name, i) => {
    const x = n((b.width - span) / 2 + i * (b.size + b.gap));
    return `<svg x="${x}" y="${n(b.row - b.size / 2)}" width="${b.size}" height="${b.size}" viewBox="0 0 96 96">
      <clipPath id="w${i}"><circle cx="48" cy="48" r="48"/></clipPath>
      <circle class="ground" cx="48" cy="48" r="48"/>
      <g clip-path="url(#w${i})">${name === 'cord' ? cord : shapes[name]}</g>
    </svg>`;
  });
  return `<!doctype html><meta charset="utf-8"><style>
    @font-face { font-family: "Instrument Serif"; src: url("${serif}") format("woff2"); }
    * { margin: 0; }
    body { background: ${ground}; }
    svg { display: block; }
    svg * { fill: none; stroke: ${ink}; stroke-width: ${n(1.2 * b.scale)}px; stroke-linecap: round;
      stroke-linejoin: round; vector-effect: non-scaling-stroke; }
    .dot { stroke-width: ${n(3.5 * b.scale)}px; }
    .peg { stroke-width: ${n(7 * b.scale)}px; }
    .ground { fill: ${tile}; stroke: none; }
    text { fill: ${ink}; stroke: none; font: ${b.line.size}px "Instrument Serif"; text-anchor: middle; }
  </style><svg width="${b.width}" height="${b.height}">${windows.join('')}
    <text x="${b.width / 2}" y="${b.line.y}">The school of the AI era</text></svg>`;
}

const row = ['Ripple', 'Sigmoid', 'Steps', 'cord', 'Bell curve', 'Spiral', 'Cube'] as const;

// Each picture with its size: X's and LinkedIn's from their help pages, GitHub's about 500 px and
// Google's sign-in screen 120 px. The 1080 px pictures are for any site that takes a larger one.
const pictures: Record<string, { width: number; height: number; html: string }> = {};
for (const [name, colours] of Object.entries(themes)) {
  for (const [suffix, size] of [
    ['', 1080],
    ['-400', 400],
    ['-120', 120],
  ] as const) {
    pictures[`profile-${name}${suffix}`] = {
      width: size,
      height: size,
      html: profile(size, colours),
    };
  }
}
pictures['x-header'] = {
  width: 1500,
  height: 500,
  html: banner(
    {
      width: 1500,
      height: 500,
      windows: row,
      size: 150,
      gap: 30,
      row: 200,
      line: { y: 392, size: 46 },
      scale: 2.5,
    },
    themes.dark,
  ),
};
pictures['linkedin-page-cover'] = {
  width: 1512,
  height: 256,
  html: banner(
    {
      width: 1512,
      height: 256,
      windows: ['Waves', ...row, 'Peaks'],
      size: 108,
      gap: 26,
      row: 104,
      line: { y: 214, size: 23 },
      scale: 1.34,
    },
    themes.dark,
  ),
};
pictures['linkedin-profile-cover'] = {
  width: 1584,
  height: 396,
  html: banner(
    {
      width: 1584,
      height: 396,
      windows: row,
      size: 128,
      gap: 26,
      row: 160,
      line: { y: 322, size: 36 },
      scale: 2,
    },
    themes.dark,
  ),
};

mkdirSync(out, { recursive: true });
const work = mkdtempSync(path.join(tmpdir(), 'sulba-brand-'));
const browser = await chromium.launch();
try {
  for (const [name, { width, height, html }] of Object.entries(pictures)) {
    const file = path.join(work, `${name}.html`);
    const page = html.startsWith('<svg')
      ? `<!doctype html><style>* { margin: 0; } svg { display: block; }</style>${html}`
      : html;
    writeFileSync(file, page);
    const tab = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
    await tab.goto(pathToFileURL(file).href);
    await tab.evaluate(() => document.fonts.ready);
    await tab.screenshot({ path: path.join(out, `${name}.png`) });
    await tab.close();
    console.log(`brand/${name}.png  ${width} × ${height}`);
  }
} finally {
  await browser.close();
  rmSync(work, { recursive: true, force: true });
}
for (const [name, colours] of Object.entries(themes)) {
  writeFileSync(path.join(out, `profile-${name}.svg`), `${profile(1080, colours)}\n`);
  console.log(`brand/profile-${name}.svg`);
}

import { pegs } from '@sulba/ui/mark';
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { expect, test } from 'vitest';
import CordFigure from './CordFigure.astro';

type Point = (typeof pegs)[number];

const render = async () => (await AstroContainer.create()).renderToString(CordFigure);

const labels = (html: string) =>
  [...html.matchAll(/<text x="([\d.-]+)" y="([\d.-]+)"[^>]*>\s*(\d+)\s*<\/text>/g)].map(
    ([, x, y, text]) => ({ at: [Number(x), Number(y)] as const, text: Number(text) }),
  );

// Which side of the line through a and b the point p lies on.
const side = (a: Point, b: Point, p: Point) =>
  Math.sign((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]));

test('the figure marks all 12 lengths of cord: 3 pegs and 9 knots', async () => {
  const html = await render();

  expect(html.match(/class="peg"/g)).toHaveLength(3);
  expect(html.match(/class="knot"/g)).toHaveLength(9);
});

test('each side is labelled with its length, outside the triangle', async () => {
  const [top, corner, end] = pegs;
  const found = labels(await render());

  expect(found.map(({ text }) => text)).toEqual([3, 4, 5]);
  const sides = [
    [top, corner, end],
    [corner, end, top],
    [end, top, corner],
  ] as const;

  for (const [i, [from, to, opposite]] of sides.entries()) {
    const at = found[i]?.at;
    if (!at) throw new Error(`side ${i + 1} has no label`);
    expect(side(from, to, at)).toBe(-side(from, to, opposite));
  }
});

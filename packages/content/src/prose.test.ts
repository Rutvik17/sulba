import { expect, test } from 'vitest';
import { drawnCharacters, italicOf } from './glyphs.ts';
import { renderProse } from './prose.ts';

const fence = (tex: string) => `${'```'}math\n${tex}\n${'```'}\n`;

test('a math block renders as display MathML, and inline math in dollars sits in the text', () => {
  const { html, errors, formulas } = renderProse(
    `${fence(String.raw`\sigma(z) = \frac{1}{1 + e^{-z}}`)}\nThe sigmoid ${String.raw`${'`'}$\sigma(z)$${'`'}`} is a probability.`,
    {},
  );
  expect(errors).toEqual([]);
  expect(formulas).toHaveLength(2);
  expect(html).toContain('<math display="block"');
  expect(html).toContain('<mfrac>');
  expect(html).toMatch(/The sigmoid <math>.*<mi>σ<\/mi>.*<\/math> is a probability\./);
});

test('a table and a formula on its own lines each sit in a box that can scroll sideways', () => {
  const { html, errors } = renderProse(
    `${fence('n + 1')}\nThe count ${'`'}$n$${'`'}.\n\n| Votes | Yes |\n| --- | --- |\n| 3 | 2 |\n`,
    {},
  );
  expect(errors).toEqual([]);
  expect(html).toMatch(
    /^<article><div data-scroll=""><math display="block".*?<\/math><\/div><p>The count <math><mi>n<\/mi><\/math>\.<\/p>/s,
  );
  expect(html).toMatch(/<div data-scroll=""><table><thead>.*<\/table><\/div><\/article>$/s);
});

test('code that isn’t maths stays code', () => {
  const { html } = renderProse(
    `Call ${'`'}sigmoid(z)${'`'}.\n\n${'```'}python\nprint(1)\n${'```'}\n`,
    {},
  );
  expect(html).toContain('<code>sigmoid(z)</code>');
  expect(html).toContain('<pre><code data-language="python">print(1)\n</code></pre>');
});

test('figures fill \\fig{} in formulas and $fig in the text, and are counted as shown', () => {
  const { html, used, errors } = renderProse(
    `${fence(String.raw`\sigma(2) = \fig{sigma_2}`)}\nIt is {% $fig.sigma_2 %}, out of {% $fig.top %}.`,
    { sigma_2: '0.8808', top: '1' },
  );
  expect(errors).toEqual([]);
  expect(html).toContain('<mn>0.8808</mn>');
  expect(html).toContain('It is 0.8808, out of 1.');
  expect([...used].sort()).toEqual(['sigma_2', 'top']);
});

test('a formula that doesn’t render, and a figure that doesn’t exist, are errors', () => {
  const { errors } = renderProse(
    `${fence(String.raw`\frac{1}{`)}\n${String.raw`${'`'}$\fig{nope}$${'`'}`} and {% $fig.gone %}.`,
    {},
  );
  expect(errors).toEqual([
    "Undefined variable: 'fig.gone'",
    expect.stringMatching(/^The formula \\frac\{1\}\{ doesn't render: /),
    '\\fig{nope}: figures.py gives no nope.',
  ]);
});

test('one line of text renders without a paragraph, and more than one is an error', () => {
  const line = renderProse(
    'Fast on {% $fig.many %} votes, in `$\\fig{limit}\\,\\text{s}$`',
    {
      many: '60,000',
      limit: '1',
    },
    { oneLine: true },
  );
  expect(line.errors).toEqual([]);
  expect(line.html).toMatch(/^Fast on 60,000 votes, in <math>.*<mn>1<\/mn>.*<\/math>$/);
  expect(renderProse('One.\n\nTwo.', {}, { oneLine: true }).errors).toEqual([
    'This text is one line, alone.',
  ]);
});

test('a one-letter identifier is drawn in its math italic form, as MathML Core says', () => {
  expect(String.fromCodePoint(italicOf('x'.codePointAt(0) as number))).toBe('𝑥');
  expect(String.fromCodePoint(italicOf('h'.codePointAt(0) as number))).toBe('ℎ');
  expect(String.fromCodePoint(italicOf('W'.codePointAt(0) as number))).toBe('𝑊');
  expect(String.fromCodePoint(italicOf('σ'.codePointAt(0) as number))).toBe('𝜎');
  expect(String.fromCodePoint(italicOf('Ω'.codePointAt(0) as number))).toBe('𝛺');
  expect(String.fromCodePoint(italicOf('∂'.codePointAt(0) as number))).toBe('𝜕');
  expect(String.fromCodePoint(italicOf('ϵ'.codePointAt(0) as number))).toBe('𝜖');
  expect(italicOf('1'.codePointAt(0) as number)).toBe('1'.codePointAt(0));
});

test('the characters a formula draws: italic letters, upright names, no invisible operators', () => {
  const [mathml = ''] = renderProse(
    fence(String.raw`\operatorname{softmax}(x)_i = \frac{e^{x_i}}{\sum_j e^{x_j}}`),
    {},
  ).formulas;
  const drawn = [...drawnCharacters(mathml)].map((point) => String.fromCodePoint(point));
  expect(drawn.sort()).toEqual(
    ['(', ')', '=', '∑', 'a', 'f', 'm', 'o', 's', 't', 'x', '𝑒', '𝑖', '𝑗', '𝑥'].sort(),
  );
});

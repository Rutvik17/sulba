import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { expect, test } from 'vitest';
import TopBar from './TopBar.astro';

const render = async (path: string) =>
  (await AstroContainer.create()).renderToString(TopBar, {
    request: new Request(`https://sulba.dev${path}`),
  });

const review = (html: string) => /<a class="link" href="\/academy\/review\/"[^>]*>/.exec(html)?.[0];

test("the top bar's name leads to the Academy, and its Review link to the Review page", async () => {
  const html = await render('/about/');

  expect(html).toMatch(/<a class="brand" href="\/academy\/"/);
  expect(review(html)).toBeDefined();
  expect(review(html)).not.toContain('aria-current');
});

test('the top bar marks Review as the page you are on, on the Review page', async () => {
  expect(review(await render('/academy/review/'))).toContain('aria-current="page"');
});

import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { expect, test } from 'vitest';
import Page from './Page.astro';

test('Page puts its title in the document head and marks the page as English', async () => {
  const container = await AstroContainer.create();

  const html = await container.renderToString(Page, { props: { title: 'Lesson one · Sulba' } });

  expect(html).toContain('<title>Lesson one · Sulba</title>');
  expect(html).toContain('<html lang="en">');
});

test('Page renders its content inside the main landmark', async () => {
  const container = await AstroContainer.create();

  const html = await container.renderToString(Page, {
    props: { title: 'Sulba' },
    slots: { default: '<p>Session content</p>' },
  });

  expect(html).toMatch(/<main>\s*<p>Session content<\/p>\s*<\/main>/);
});

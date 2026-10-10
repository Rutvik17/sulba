import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { expect, test } from 'vitest';
import Page from './Page.astro';

test('Page puts its title in the document head and marks the page as English', async () => {
  const container = await AstroContainer.create();

  const html = await container.renderToString(Page, { props: { title: 'Lesson one · Sulba' } });

  expect(html).toContain('<title>Lesson one · Sulba</title>');
  expect(html).toMatch(/<html lang="en"[\s>]/);
});

test('Page renders its content inside the main landmark', async () => {
  const container = await AstroContainer.create();

  const html = await container.renderToString(Page, {
    props: { title: 'Sulba' },
    slots: { default: '<p>Session content</p>' },
  });

  expect(html).toMatch(/<main id="main"[^>]*>\s*<p>Session content<\/p>\s*<\/main>/);
});

test('Page starts with a link that skips past the top bar to the content', async () => {
  const container = await AstroContainer.create();

  const html = await container.renderToString(Page, { props: { title: 'Sulba' } });
  const body = html.slice(html.indexOf('<body'));

  expect(body).toMatch(/^<body[^>]*>\s*<a [^>]*href="#main"[^>]*>Skip to content<\/a>/);
});

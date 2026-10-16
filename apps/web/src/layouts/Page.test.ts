import { palettes } from '@sulba/editor/palettes';
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

test("the theme panel offers the editor's themes on a page with an editor, and only there", async () => {
  const container = await AstroContainer.create();

  const plain = await container.renderToString(Page, { props: { title: 'Sulba' } });
  const lab = await container.renderToString(Page, { props: { title: 'Sulba', editor: true } });

  expect(plain).not.toContain('Editor theme');
  expect(plain).not.toContain('name="editor-theme"');
  expect(lab).toMatch(/<legend[^>]*>Editor theme<\/legend>/);
  expect(lab.match(/name="editor-theme"/g)).toHaveLength(palettes.length);
});

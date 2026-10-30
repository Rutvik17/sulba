import { readdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';
import { expect, test } from 'vitest';

// Once wrangler.jsonc has run_worker_first, Cloudflare answers every address it doesn't send to
// the Worker from the static assets, with their 404 page or a 405 (decision record 55). So each
// route the Worker renders must be one of its addresses.

const pages = fileURLToPath(new URL('pages/', import.meta.url));

const rules: string[] = ts.parseConfigFileTextToJson(
  'wrangler.jsonc',
  await readFile(new URL('../wrangler.jsonc', import.meta.url), 'utf8'),
).config.assets.run_worker_first;

/** A rule as Cloudflare's router reads it: `*` stands for any characters, `/` among them. */
const matches = (rule: string, path: string) =>
  new RegExp(`^${rule.split('*').map(RegExp.escape).join('.*')}$`).test(path);

/** Whether a request for the path reaches the Worker before the static assets. */
const workerFirst = (path: string) =>
  !rules.some((rule) => rule.startsWith('!') && matches(rule.slice(1), path)) &&
  rules.some((rule) => !rule.startsWith('!') && matches(rule, path));

/** An address a page or endpoint answers, with each parameter filled in. */
const addressOf = (file: string) =>
  `/${file.replace(/\.(ts|astro)$/, '')}`
    .replace(/\/index$/, '/')
    .replace(/\[\.\.\.[^\]]+\]/g, 'a/b')
    .replace(/\[[^\]]+\]/g, 'a');

const files = (await readdir(pages, { recursive: true })).filter((file) =>
  /\.(ts|astro)$/.test(file),
);
const rendered = await Promise.all(
  files.map(async (file) => ({
    address: addressOf(file),
    onWorker: /export const prerender = false/.test(await readFile(`${pages}${file}`, 'utf8')),
  })),
);

test('every route the Worker renders is sent to it first', () => {
  const routes = rendered.filter(({ onWorker }) => onWorker).map(({ address }) => address);

  expect(routes).toContain('/mcp');
  expect(routes.filter((address) => !workerFirst(address))).toEqual([]);
});

test('pages built ahead of time and the app’s files are served without the Worker', () => {
  const built = rendered.filter(({ onWorker }) => !onWorker).map(({ address }) => address);

  expect(built).toContain('/privacy');
  expect([...built, '/app/assets/index.js', '/academy/'].filter(workerFirst)).toEqual([]);
});

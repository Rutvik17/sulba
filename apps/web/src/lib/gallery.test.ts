import { expect, test } from 'vitest';
import { gallery } from '../../gallery';

/** The routes the gallery integration adds for a command, with or without SULBA_GALLERY=on. */
function routes(command: 'dev' | 'build', requested: boolean): string[] {
  const added: string[] = [];
  const setup = gallery(requested).hooks['astro:config:setup'];
  type Options = Parameters<NonNullable<typeof setup>>[0];
  const injectRoute = ({ pattern }: { pattern: string }) => added.push(pattern);
  setup?.({ command, injectRoute } as unknown as Options);
  return added;
}

test('a build for sulba.dev has no gallery', () => {
  expect(routes('build', false)).toEqual([]);
});

test('a build that asks for the gallery has it at /gallery', () => {
  expect(routes('build', true)).toEqual(['/gallery']);
});

test('the development server always has the gallery', () => {
  expect(routes('dev', false)).toEqual(['/gallery']);
});

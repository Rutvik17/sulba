import { afterEach, expect, test, vi } from 'vitest';
import type { LabView } from '../lib/labs';
import { labData } from './data';

function labWith(id: string): LabView {
  const set = (file: string) => ({
    file,
    title: file,
    creators: [],
    url: `/data/0123456789abcdef/${file}`,
    licence: { name: 'CC BY 4.0', url: 'https://creativecommons.org/licenses/by/4.0/' },
    changes: '',
    path: `data/${file}`,
  });
  return {
    id,
    path: 'course/module/lab',
    title: 'Lab',
    summary: 'A lab.',
    course: 'Course',
    level: 'Level',
    module: 'Module',
    data: [set('votes.csv'), set('seats.csv')],
    stages: [],
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

test("a lab's datasets are fetched once, and each run shares them by path", async () => {
  const fetched = vi.fn(async (url: string) => new Response(`text of ${url}`));
  vi.stubGlobal('fetch', fetched);
  const lab = labWith('lab_once01');
  const first = await labData(lab);
  const second = await labData(lab);
  expect(first).toEqual({
    'data/votes.csv': 'text of /data/0123456789abcdef/votes.csv',
    'data/seats.csv': 'text of /data/0123456789abcdef/seats.csv',
  });
  expect(second).toBe(first);
  expect(fetched).toHaveBeenCalledTimes(2);
});

test('a fetch that fails is tried again the next time', async () => {
  const failing = vi.fn(async () => new Response('', { status: 503 }));
  vi.stubGlobal('fetch', failing);
  const lab = labWith('lab_again1');
  await expect(labData(lab)).rejects.toThrow('/data/0123456789abcdef/votes.csv answered 503.');
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response('choice\nyes\n')),
  );
  expect(await labData(lab)).toEqual({
    'data/votes.csv': 'choice\nyes\n',
    'data/seats.csv': 'choice\nyes\n',
  });
});

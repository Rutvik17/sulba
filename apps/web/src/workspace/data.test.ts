import { afterEach, expect, test, vi } from 'vitest';
import type { LabView } from '../lib/labs';
import { labData, projectFiles } from './data';

function labWith(id: string): LabView {
  const set = (file: string) => ({
    file,
    title: file,
    creators: [],
    url: `https://example.com/${file}`,
    licence: { name: 'CC BY 4.0', url: 'https://creativecommons.org/licenses/by/4.0/' },
    changes: '',
    path: `data/${file}`,
    served: `/data/0123456789abcdef/${file}`,
  });
  return {
    id,
    path: 'course/module/lab',
    runs: 'browser',
    title: 'Lab',
    summary: 'A lab.',
    course: 'Course',
    level: 'Level',
    module: 'Module',
    data: [set('votes.csv'), set('seats.csv')],
    references: [
      { path: 'references/shares.json', served: '/references/fedcba9876543210/shares.json' },
    ],
    project: [
      { name: 'pyproject.toml', served: '/project/0123456789abcdef/pyproject.toml' },
      { name: 'uv.lock', served: '/project/fedcba9876543210/uv.lock' },
    ],
    stages: [],
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

test("a lab's datasets and references are fetched once, and each run shares them by path", async () => {
  const fetched = vi.fn(async (url: string) => new Response(`text of ${url}`));
  vi.stubGlobal('fetch', fetched);
  const lab = labWith('lab_once01');
  const first = await labData(lab);
  const second = await labData(lab);
  expect(first).toEqual({
    'data/votes.csv': 'text of /data/0123456789abcdef/votes.csv',
    'data/seats.csv': 'text of /data/0123456789abcdef/seats.csv',
    'references/shares.json': 'text of /references/fedcba9876543210/shares.json',
  });
  expect(second).toBe(first);
  expect(fetched).toHaveBeenCalledTimes(3);
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
    'references/shares.json': 'choice\nyes\n',
  });
});

test("a lab's project files are fetched once, apart from its datasets, by name", async () => {
  const fetched = vi.fn(async (url: string) => new Response(`text of ${url}`));
  vi.stubGlobal('fetch', fetched);
  const lab = labWith('lab_proj01');
  await labData(lab);
  const first = await projectFiles(lab);
  expect(first).toEqual({
    'pyproject.toml': 'text of /project/0123456789abcdef/pyproject.toml',
    'uv.lock': 'text of /project/fedcba9876543210/uv.lock',
  });
  expect(await projectFiles(lab)).toBe(first);
  expect(fetched).toHaveBeenCalledTimes(5);
});

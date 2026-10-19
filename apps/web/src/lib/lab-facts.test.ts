import { expect, test } from 'vitest';
import {
  aboutTime,
  fetchedOf,
  labFacts,
  levelFacts,
  moduleFacts,
  servedOf,
  sizeOf,
} from './lab-facts';
import type { LabView } from './labs';

const stage = (kind: LabView['stages'][number]['kind'], file: string, minutes: number) =>
  ({ kind, file, minutes }) as LabView['stages'][number];

test('a lab under an hour is given in minutes, and a longer one to the nearest half hour', () => {
  expect(aboutTime(20)).toBe('About 20 minutes');
  expect(aboutTime(60)).toBe('About 1 hour');
  expect(aboutTime(100)).toBe('About 1.5 hours');
  expect(aboutTime(240)).toBe('About 4 hours');
});

test("a lab's facts name its files in order, count its stages by kind and add up its time", () => {
  const stages = [
    stage('build', 'tally.py', 20),
    stage('build', 'tally.py', 20),
    stage('catch', 'report.py', 15),
    stage('ship', 'report.py', 15),
  ];
  expect(labFacts({ stages })).toEqual([
    { term: 'You build', value: 'tally.py, then report.py' },
    { term: 'Stages', value: '2 Build, 1 Catch, 1 Ship' },
    { term: 'Time', value: 'About 1 hour' },
  ]);
});

test("a lab that runs on the learner's machine says so", () => {
  const stages = [stage('build', 'model.py', 30)];
  expect(labFacts({ stages, runs: 'machine' }).at(-1)).toEqual({
    term: 'Runs on',
    value: 'Your machine',
  });
  expect(labFacts({ stages, runs: 'browser' })).toHaveLength(3);
});

test('a size is given in decimal units, to a tenth', () => {
  expect([512, 5148, 26_421_880, 1_500_000_000].map(sizeOf)).toEqual([
    '512 bytes',
    '5.1 kB',
    '26.4 MB',
    '1.5 GB',
  ]);
});

test("a machine lab's first run downloads its fetched files, from their hosts in order", () => {
  const file = (url: string, bytes: number) => ({ file: 'x', url, bytes, sha256: '0'.repeat(64) });
  const source = (files: ReturnType<typeof file>[]) =>
    ({ kind: 'data', title: 'Tiles', files }) as LabView['fetch'][number];
  expect(fetchedOf({ fetch: [] })).toBeNull();
  const fetch = [
    source([file('https://zenodo.org/a.zip', 94_658_721)]),
    source([
      file('https://dl.fbaipublicfiles.com/b.pth', 88_283_115),
      file('https://zenodo.org/c.zip', 1_000),
    ]),
  ];
  expect(fetchedOf({ fetch })).toEqual({
    size: '182.9 MB',
    hosts: 'zenodo.org and dl.fbaipublicfiles.com',
  });
});

test("a lab's model is named with the size of its file and the host it comes from", () => {
  expect(servedOf({ model: null })).toBeNull();
  const model = {
    title: 'Qwen3.5-0.8B',
    creators: ['Qwen'],
    url: 'https://huggingface.co/Qwen/Qwen3.5-0.8B',
    licence: { name: 'Apache License 2.0', url: 'https://www.apache.org/licenses/LICENSE-2.0' },
    file: {
      url: 'https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF/resolve/8fea620/Qwen3.5-0.8B-Q8_0.gguf',
      bytes: 833_592_096,
      sha256: 'a'.repeat(64),
    },
  };
  expect(servedOf({ model })).toEqual({
    title: 'Qwen3.5-0.8B',
    size: '833.6 MB',
    host: 'huggingface.co',
  });
});

test('problems are counted as one Problem or as Problems', () => {
  const one = [stage('problem', 'pairs.py', 20)];
  expect(labFacts({ stages: one })[1]).toEqual({ term: 'Stages', value: '1 Problem' });
  const two = [...one, stage('problem', 'windows.py', 25)];
  expect(labFacts({ stages: two })[1]).toEqual({ term: 'Stages', value: '2 Problems' });
});

test("a module's row counts its labs and adds up their time", () => {
  const lab = { stages: [stage('build', 'tally.py', 50), stage('ship', 'tally.py', 40)] };
  expect(moduleFacts([lab])).toBe('1 lab · About 1.5 hours');
  expect(moduleFacts([lab, lab, lab])).toBe('3 labs · About 4.5 hours');
});

test("a level's facts count its modules and labs, add up their time and say what it needs", () => {
  const lab = { stages: [stage('build', 'tally.py', 30), stage('catch', 'report.py', 15)] };
  const level = {
    needs: 'Any laptop: every lab runs in your browser',
    modules: [{ labs: [lab, lab] }, { labs: [lab] }],
  };
  expect(levelFacts(level)).toEqual([
    { term: 'Modules', value: '2' },
    { term: 'Labs', value: '3' },
    { term: 'Time', value: 'About 2.5 hours' },
    { term: 'Needs', value: 'Any laptop: every lab runs in your browser' },
  ]);
});

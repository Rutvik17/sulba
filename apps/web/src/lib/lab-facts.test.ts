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

test('a Design stage builds no file, so a lab of designs names none', () => {
  const designs = [stage('design', '', 45), stage('design', '', 45)];
  expect(labFacts({ stages: designs })).toEqual([
    { term: 'Stages', value: '2 Designs' },
    { term: 'Time', value: 'About 1.5 hours' },
  ]);
  const mixed = [stage('problem', 'pairs.py', 20), stage('design', '', 30)];
  expect(labFacts({ stages: mixed }).slice(0, 2)).toEqual([
    { term: 'You build', value: 'pairs.py' },
    { term: 'Stages', value: '1 Problem, 1 Design' },
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

test("a lab's models are named with the size of their files and the hosts they come from", () => {
  expect(servedOf({ models: [] })).toBeNull();
  const licence = {
    name: 'Apache License 2.0',
    url: 'https://www.apache.org/licenses/LICENSE-2.0',
  };
  const chat = {
    title: 'Qwen3.5-0.8B',
    kind: 'chat' as const,
    creators: ['Qwen'],
    url: 'https://huggingface.co/Qwen/Qwen3.5-0.8B',
    licence,
    file: {
      url: 'https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF/resolve/8fea620/Qwen3.5-0.8B-Q8_0.gguf',
      bytes: 833_592_096,
      sha256: 'a'.repeat(64),
    },
  };
  expect(servedOf({ models: [chat] })).toEqual({
    count: 1,
    titles: 'Qwen3.5-0.8B',
    size: '833.6 MB',
    hosts: 'huggingface.co',
  });
  const embedding = {
    ...chat,
    title: 'nomic-embed-text-v1.5',
    kind: 'embedding' as const,
    file: { ...chat.file, url: 'https://example.com/nomic.gguf', bytes: 146_146_432 },
  };
  const reranking = {
    ...chat,
    title: 'Qwen3-Reranker-0.6B',
    kind: 'reranking' as const,
    file: { ...chat.file, bytes: 639_153_184 },
  };
  expect(servedOf({ models: [chat, embedding, reranking] })).toEqual({
    count: 3,
    titles: 'Qwen3.5-0.8B, nomic-embed-text-v1.5 and Qwen3-Reranker-0.6B',
    size: '1.6 GB',
    hosts: 'huggingface.co and example.com',
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
  expect(moduleFacts({ optional: false, labs: [lab] })).toBe('1 lab · About 1.5 hours');
  expect(moduleFacts({ optional: false, labs: [lab, lab, lab] })).toBe('3 labs · About 4.5 hours');
});

test("an optional module's row says so first", () => {
  const lab = { stages: [stage('build', 'tally.py', 50)] };
  expect(moduleFacts({ optional: true, labs: [lab] })).toBe('Optional · 1 lab · About 50 minutes');
});

test("a level's facts count its modules and labs, add up their time and say what it needs", () => {
  const lab = { stages: [stage('build', 'tally.py', 30), stage('catch', 'report.py', 15)] };
  const level = {
    needs: 'Any laptop: every lab runs in your browser',
    modules: [
      { optional: false, labs: [lab, lab] },
      { optional: false, labs: [lab] },
    ],
  };
  expect(levelFacts(level)).toEqual([
    { term: 'Modules', value: '2' },
    { term: 'Labs', value: '3' },
    { term: 'Time', value: 'About 2.5 hours' },
    { term: 'Needs', value: 'Any laptop: every lab runs in your browser' },
  ]);
});

test("a level's facts say how many of its modules are optional, and give their time apart", () => {
  const lab = { stages: [stage('build', 'tally.py', 30), stage('catch', 'report.py', 15)] };
  const needs = 'Any laptop: every lab runs in your browser';
  const one = levelFacts({
    needs,
    modules: [
      { optional: false, labs: [lab, lab] },
      { optional: true, labs: [lab] },
    ],
  });
  expect(one.slice(0, 3)).toEqual([
    { term: 'Modules', value: '2, 1 of them optional' },
    { term: 'Labs', value: '3' },
    { term: 'Time', value: 'About 1.5 hours, and about 45 minutes more in the optional module' },
  ]);
  const two = levelFacts({
    needs,
    modules: [
      { optional: false, labs: [lab] },
      { optional: true, labs: [lab, lab] },
      { optional: true, labs: [lab, lab] },
    ],
  });
  expect(two.slice(0, 3)).toEqual([
    { term: 'Modules', value: '3, 2 of them optional' },
    { term: 'Labs', value: '5' },
    { term: 'Time', value: 'About 45 minutes, and about 3 hours more in the optional modules' },
  ]);
});

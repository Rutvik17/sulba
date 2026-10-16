import { expect, test } from 'vitest';
import { aboutTime, labFacts } from './lab-facts';
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

test('problems are counted as one Problem or as Problems', () => {
  const one = [stage('problem', 'pairs.py', 20)];
  expect(labFacts({ stages: one })[1]).toEqual({ term: 'Stages', value: '1 Problem' });
  const two = [...one, stage('problem', 'windows.py', 25)];
  expect(labFacts({ stages: two })[1]).toEqual({ term: 'Stages', value: '2 Problems' });
});

import { expect, test } from 'vitest';
import { aboutTime, labFacts, levelFacts, moduleFacts } from './lab-facts';
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

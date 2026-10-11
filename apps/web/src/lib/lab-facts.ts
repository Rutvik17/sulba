import type { LabView } from './labs';

const kindNames = { build: 'Build' } as const;

/** "About 45 minutes", or in hours to the nearest half past an hour: "About 4.5 hours". */
export function aboutTime(minutes: number): string {
  if (minutes < 60) return `About ${minutes} minutes`;
  const hours = Math.round(minutes / 30) / 2;
  return `About ${hours} ${hours === 1 ? 'hour' : 'hours'}`;
}

/** What the facts under a lab's title say: the files built, the stages, the time. */
export function labFacts(lab: LabView): { term: string; value: string }[] {
  const files = [...new Set(lab.stages.map((stage) => stage.file))];
  const kinds = Object.entries(kindNames)
    .map(([kind, name]) => ({
      name,
      count: lab.stages.filter((stage) => stage.kind === kind).length,
    }))
    .filter(({ count }) => count > 0)
    .map(({ name, count }) => `${count} ${name}`);
  const minutes = lab.stages.reduce((sum, stage) => sum + stage.minutes, 0);
  return [
    { term: 'You build', value: files.join(', then ') },
    { term: 'Stages', value: kinds.join(', ') },
    { term: 'Time', value: aboutTime(minutes) },
  ];
}

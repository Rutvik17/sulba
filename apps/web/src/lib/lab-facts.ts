import type { LabView } from './labs';

type Kind = LabView['stages'][number]['kind'];

/** Each kind of stage's name, for one stage and for more. */
const kindNames: Readonly<Record<Kind, readonly [string, string]>> = {
  build: ['Build', 'Build'],
  catch: ['Catch', 'Catch'],
  ship: ['Ship', 'Ship'],
  problem: ['Problem', 'Problems'],
};

/** "About 45 minutes", or in hours to the nearest half past an hour: "About 4.5 hours". */
export function aboutTime(minutes: number): string {
  if (minutes < 60) return `About ${minutes} minutes`;
  const hours = Math.round(minutes / 30) / 2;
  return `About ${hours} ${hours === 1 ? 'hour' : 'hours'}`;
}

type Fact = { term: string; value: string };

/** The minutes a lab takes: its stages' minutes, added up. */
export function minutesOf(lab: Pick<LabView, 'stages'>): number {
  return lab.stages.reduce((sum, stage) => sum + stage.minutes, 0);
}

/**
 * What the facts under a lab's title say: the files built, the stages, the time, and for a lab that
 * runs on the learner's machine, that it runs there.
 */
export function labFacts(lab: Pick<LabView, 'stages'> & Partial<Pick<LabView, 'runs'>>): Fact[] {
  const files = [...new Set(lab.stages.map((stage) => stage.file))];
  const kinds = Object.entries(kindNames)
    .map(([kind, names]) => ({
      names,
      count: lab.stages.filter((stage) => stage.kind === kind).length,
    }))
    .filter(({ count }) => count > 0)
    .map(({ names: [one, more], count }) => `${count} ${count === 1 ? one : more}`);
  return [
    { term: 'You build', value: files.join(', then ') },
    { term: 'Stages', value: kinds.join(', ') },
    { term: 'Time', value: aboutTime(minutesOf(lab)) },
    ...(lab.runs === 'machine' ? [{ term: 'Runs on', value: 'Your machine' }] : []),
  ];
}

/** A size in bytes in decimal units, as a download shows it: "5.1 kB", "26.4 MB". */
export function sizeOf(bytes: number): string {
  for (const [unit, scale] of [
    ['GB', 1e9],
    ['MB', 1e6],
    ['kB', 1e3],
  ] as const) {
    if (bytes >= scale) return `${(bytes / scale).toFixed(1)} ${unit}`;
  }
  return `${bytes} bytes`;
}

/** Items in words: "a", "a and b", "a, b and c". */
function inWords(items: readonly string[]): string {
  return items.length > 1
    ? `${items.slice(0, -1).join(', ')} and ${items.at(-1)}`
    : (items[0] ?? '');
}

/**
 * What a machine lab's first run downloads (decision record 29): the size of the files it fetches,
 * and the hosts they come from in the order the lab lists them. Null when it fetches none.
 */
export function fetchedOf(lab: Pick<LabView, 'fetch'>): { size: string; hosts: string } | null {
  const files = lab.fetch.flatMap((source) => source.files);
  if (files.length === 0) return null;
  const bytes = files.reduce((sum, file) => sum + file.bytes, 0);
  const hosts = [...new Set(files.map((file) => new URL(file.url).hostname))];
  return { size: sizeOf(bytes), hosts: inWords(hosts) };
}

/** What a module's row says under its title: how many labs it has, and their time. */
export function moduleFacts(labs: readonly Pick<LabView, 'stages'>[]): string {
  const minutes = labs.reduce((sum, lab) => sum + minutesOf(lab), 0);
  return `${labs.length} ${labs.length === 1 ? 'lab' : 'labs'} · ${aboutTime(minutes)}`;
}

/** The facts above a level's modules: how many modules and labs, their time, and what it needs. */
export function levelFacts(level: {
  readonly needs: string;
  readonly modules: readonly { readonly labs: readonly Pick<LabView, 'stages'>[] }[];
}): Fact[] {
  const labs = level.modules.flatMap((module) => module.labs);
  const minutes = labs.reduce((sum, lab) => sum + minutesOf(lab), 0);
  return [
    { term: 'Modules', value: String(level.modules.length) },
    { term: 'Labs', value: String(labs.length) },
    { term: 'Time', value: aboutTime(minutes) },
    { term: 'Needs', value: level.needs },
  ];
}

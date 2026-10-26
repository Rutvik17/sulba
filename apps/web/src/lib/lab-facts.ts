import type { LabView } from './labs';

type Kind = LabView['stages'][number]['kind'];

/** Each kind of stage's name, for one stage and for more. */
const kindNames: Readonly<Record<Kind, readonly [string, string]>> = {
  build: ['Build', 'Build'],
  catch: ['Catch', 'Catch'],
  ship: ['Ship', 'Ship'],
  problem: ['Problem', 'Problems'],
  design: ['Design', 'Designs'],
};

/** "45 minutes", or in hours to the nearest half past an hour: "4.5 hours". */
function timeOf(minutes: number): string {
  if (minutes < 60) return `${minutes} minutes`;
  const hours = Math.round(minutes / 30) / 2;
  return `${hours} ${hours === 1 ? 'hour' : 'hours'}`;
}

/** "About 45 minutes", or in hours to the nearest half past an hour: "About 4.5 hours". */
export function aboutTime(minutes: number): string {
  return `About ${timeOf(minutes)}`;
}

type Fact = { term: string; value: string };

/** The minutes a lab takes: its stages' minutes, added up. */
export function minutesOf(lab: Pick<LabView, 'stages'>): number {
  return lab.stages.reduce((sum, stage) => sum + stage.minutes, 0);
}

/**
 * What the facts under a lab's title say: the files built, if it builds any, the stages, the time,
 * and for a lab that runs on the learner's machine, that it runs there. A Design stage builds no
 * file.
 */
export function labFacts(lab: Pick<LabView, 'stages'> & Partial<Pick<LabView, 'runs'>>): Fact[] {
  const files = [...new Set(lab.stages.map((stage) => stage.file).filter((file) => file !== ''))];
  const kinds = Object.entries(kindNames)
    .map(([kind, names]) => ({
      names,
      count: lab.stages.filter((stage) => stage.kind === kind).length,
    }))
    .filter(({ count }) => count > 0)
    .map(({ names: [one, more], count }) => `${count} ${count === 1 ? one : more}`);
  return [
    ...(files.length > 0 ? [{ term: 'You build', value: files.join(', then ') }] : []),
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

/**
 * What a machine lab's `uv run sulba.py model` serves and downloads the first time (decision record
 * 34): how many models, their names, the size of their files and the hosts they come from, in the
 * order the lab lists them. Null when it has none.
 */
export function servedOf(
  lab: Pick<LabView, 'models'>,
): { count: number; titles: string; size: string; hosts: string } | null {
  if (lab.models.length === 0) return null;
  const bytes = lab.models.reduce((sum, model) => sum + model.file.bytes, 0);
  const hosts = [...new Set(lab.models.map((model) => new URL(model.file.url).hostname))];
  return {
    count: lab.models.length,
    titles: inWords(lab.models.map((model) => model.title)),
    size: sizeOf(bytes),
    hosts: inWords(hosts),
  };
}

interface ModuleLabs {
  readonly optional: boolean;
  readonly labs: readonly Pick<LabView, 'stages'>[];
}

/** The minutes a module's labs take, added up. */
function minutesIn(modules: readonly ModuleLabs[]): number {
  return modules.flatMap((module) => module.labs).reduce((sum, lab) => sum + minutesOf(lab), 0);
}

/** What a module's row says under its title: whether it's optional, its labs and their time. */
export function moduleFacts(module: ModuleLabs): string {
  const { length } = module.labs;
  return [
    ...(module.optional ? ['Optional'] : []),
    `${length} ${length === 1 ? 'lab' : 'labs'}`,
    aboutTime(minutesIn([module])),
  ].join(' · ');
}

/**
 * The facts above a level's modules: how many modules, and how many of them are optional; how many
 * labs; their time, with the optional modules' apart; and what it needs.
 */
export function levelFacts(level: {
  readonly needs: string;
  readonly modules: readonly ModuleLabs[];
}): Fact[] {
  const optional = level.modules.filter((module) => module.optional);
  const required = level.modules.filter((module) => !module.optional);
  let modules = String(level.modules.length);
  let time = aboutTime(minutesIn(required));
  if (optional.length > 0) {
    modules += `, ${optional.length} of them optional`;
    time += `, and about ${timeOf(minutesIn(optional))} more in the optional ${optional.length === 1 ? 'module' : 'modules'}`;
  }
  return [
    { term: 'Modules', value: modules },
    { term: 'Labs', value: String(level.modules.flatMap((module) => module.labs).length) },
    { term: 'Time', value: time },
    { term: 'Needs', value: level.needs },
  ];
}

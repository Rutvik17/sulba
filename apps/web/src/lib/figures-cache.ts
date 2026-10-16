// A stage's figures depend only on its files and the Python that computes them, so the site's
// build keeps them between runs, each under a hash of both: `astro check` and `astro build` compute
// them once between them, and a stage whose files haven't changed doesn't run again. The content
// check always computes every stage's figures afresh, in every runtime.
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import type { FiguresRunner } from '@sulba/content';
import type { Figures, RunRequest } from '@sulba/lab/protocol';

/** The name a set of files' figures are kept under, given the runtime that computes them. */
export function figuresKey(files: RunRequest['files'], runtime: string): string {
  const hash = createHash('sha256').update(runtime);
  for (const name of Object.keys(files).sort()) hash.update(`\0${name}\0${files[name]}`);
  return hash.digest('hex');
}

/**
 * A runner that reads from `folder` what it has computed before for the same files in the same
 * runtime, and has `compute` work out the rest, keeping what comes back. An answer with a problem
 * isn't kept, so a stage whose figures failed runs again.
 */
export function cachedFigures(
  folder: string,
  runtime: string,
  compute: FiguresRunner,
): FiguresRunner {
  return async (fileSets) => {
    const keys = fileSets.map((files) => figuresKey(files, runtime));
    const answers = await Promise.all(keys.map((key) => kept(join(folder, `${key}.json`))));
    const missing = answers.flatMap((answer, index) => (answer ? [] : [index]));
    if (missing.length === 0) return answers as Figures[];
    const computed = await compute(missing.map((index) => fileSets[index] ?? {}));
    await mkdir(folder, { recursive: true });
    await Promise.all(
      missing.map(async (index, at) => {
        const answer = computed[at];
        if (!answer) throw new Error(`No figures came back for set ${index} of ${keys.length}.`);
        answers[index] = answer;
        if (answer.problem === null) {
          await writeFile(join(folder, `${keys[index]}.json`), JSON.stringify(answer));
        }
      }),
    );
    return answers as Figures[];
  };
}

/** The figures kept at `path`, or null if there are none or they can't be read. */
async function kept(path: string): Promise<Figures | null> {
  try {
    return JSON.parse(await readFile(path, 'utf8')) as Figures;
  } catch {
    return null;
  }
}

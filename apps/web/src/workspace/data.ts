// A lab's datasets and references are served apart from its page (src/pages/data and
// src/pages/references). The workspace fetches them once a visit, as it opens, and every run and
// chart takes them from there. The files of a lab's project (src/pages/project) are fetched the
// same way, the first time the learner downloads the lab.
import type { LabView } from '../lib/labs';
import type { LabData } from './stages';

const fetched = new Map<string, Promise<Readonly<Record<string, string>>>>();

/** The text at each address, by name, fetched the first time and again after a failed fetch. */
function fetchedOnce(
  key: string,
  files: readonly (readonly [name: string, served: string])[],
): Promise<Readonly<Record<string, string>>> {
  const known = fetched.get(key);
  if (known) return known;
  const loading = Promise.all(
    files.map(async ([name, served]) => {
      const response = await fetch(served);
      if (!response.ok) throw new Error(`${served} answered ${response.status}.`);
      return [name, await response.text()] as const;
    }),
  ).then((entries) => Object.fromEntries(entries));
  fetched.set(key, loading);
  loading.catch(() => fetched.delete(key));
  return loading;
}

/** The lab's datasets and references, by their paths in a run. */
export function labData(lab: LabView): Promise<LabData> {
  return fetchedOnce(
    `${lab.id} data`,
    [...lab.data, ...lab.references].map(({ path, served }) => [path, served]),
  );
}

/** The files of the lab's project, by name. */
export function projectFiles(lab: LabView): Promise<Readonly<Record<string, string>>> {
  return fetchedOnce(
    `${lab.id} project`,
    lab.project.map(({ name, served }) => [name, served]),
  );
}

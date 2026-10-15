// A lab's datasets are served apart from its page (src/pages/data). The workspace fetches them once
// a visit, as it opens, and every run and chart takes them from there.
import type { LabView } from '../lib/labs';
import type { LabData } from './stages';

const fetched = new Map<string, Promise<LabData>>();

/** The lab's datasets, fetched the first time they're asked for, and again after a failed fetch. */
export function labData(lab: LabView): Promise<LabData> {
  const known = fetched.get(lab.id);
  if (known) return known;
  const loading = Promise.all(
    lab.data.map(async ({ path, url }) => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`${url} answered ${response.status}.`);
      return [path, await response.text()] as const;
    }),
  ).then((entries): LabData => Object.fromEntries(entries));
  fetched.set(lab.id, loading);
  loading.catch(() => fetched.delete(lab.id));
  return loading;
}

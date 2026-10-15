// Each lab's datasets, served apart from the lab's page so the page stays small. A dataset's
// folder is named for its text, so the file at an address never changes and is cached for good
// (public/_headers), and labs with the same dataset share one file.

import { getCollection } from 'astro:content';
import type { APIRoute, GetStaticPaths } from 'astro';

export const getStaticPaths = (async () => {
  const files = new Map<string, string>();
  for (const { data: lab } of await getCollection('labs')) {
    for (const set of lab.data) files.set(set.served, lab.files[set.path] ?? '');
  }
  return [...files].map(([served, text]) => {
    const [hash, file] = served.split('/').slice(-2);
    return { params: { hash, file }, props: { text } };
  });
}) satisfies GetStaticPaths;

export const GET: APIRoute = ({ props }) =>
  new Response(props.text as string, { headers: { 'Content-Type': 'text/csv; charset=utf-8' } });

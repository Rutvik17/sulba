// Each lab project's files, which a download of the lab puts beside the learner's (decision record
// 25). They're fetched only for a download, so they're served apart from the lab's page, each in a
// folder named for its text, cached for good (public/_headers), as datasets are.

import { getCollection } from 'astro:content';
import type { APIRoute, GetStaticPaths } from 'astro';

export const getStaticPaths = (async () => {
  const files = new Map<string, string>();
  for (const { data: lab } of await getCollection('labs')) {
    for (const { name, served } of lab.project) files.set(served, lab.projectFiles[name] ?? '');
  }
  return [...files].map(([served, text]) => {
    const [hash, file] = served.split('/').slice(-2);
    return { params: { hash, file }, props: { text } };
  });
}) satisfies GetStaticPaths;

export const GET: APIRoute = ({ props }) =>
  new Response(props.text as string, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });

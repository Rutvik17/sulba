// Each lab's recorded references (decision record 27), served apart from the lab's page like its
// datasets: a reference's folder is named for its text, so the file at an address never changes
// and is cached for good (public/_headers).

import { getCollection } from 'astro:content';
import type { APIRoute, GetStaticPaths } from 'astro';

export const getStaticPaths = (async () => {
  const files = new Map<string, string>();
  for (const { data: lab } of await getCollection('labs')) {
    for (const reference of lab.references) {
      files.set(reference.served, lab.files[reference.path] ?? '');
    }
  }
  return [...files].map(([served, text]) => {
    const [hash, file] = served.split('/').slice(-2);
    return { params: { hash, file }, props: { text } };
  });
}) satisfies GetStaticPaths;

export const GET: APIRoute = ({ props }) =>
  new Response(props.text as string, {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });

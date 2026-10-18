// The files machine labs fetch from their publishers (decision record 29), for checks outside a
// browser. Each is kept in one folder under its sha256, fetched the first time a check needs it,
// and checked against its sha256 once in each process that uses it, since CI keeps the folder in a
// cache that nothing signs.
import { createHash } from 'node:crypto';
import { createReadStream, createWriteStream } from 'node:fs';
import { mkdir, rename, rm, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import type { ReadableStream } from 'node:stream/web';
import { fileURLToPath } from 'node:url';
import type { FetchedFile } from './protocol.ts';

/** Where checks keep the files: in the repository's node_modules/.cache, which CI keeps. */
export const fetchedFolder = fileURLToPath(
  new URL('../../../node_modules/.cache/sulba-fetched/', import.meta.url),
);

const ready = new Map<string, Promise<string>>();

/**
 * The path of the file in `folder`, under its sha256: fetched from its publisher first when it
 * isn't there or isn't the file its sha256 names.
 */
export function fetchedPath(file: FetchedFile, folder = fetchedFolder): Promise<string> {
  const path = join(folder, file.sha256);
  let kept = ready.get(path);
  if (!kept) {
    kept = keep(file, folder, path);
    ready.set(path, kept);
    kept.catch(() => ready.delete(path));
  }
  return kept;
}

async function keep(file: FetchedFile, folder: string, path: string): Promise<string> {
  if (await holds(path, file)) return path;
  const response = await fetch(file.url);
  if (!response.ok || !response.body) throw new Error(`${file.url} answered ${response.status}.`);
  // A name of this process's own, since two checks on one machine may fetch the same file.
  const partial = `${path}.${process.pid}.partial`;
  await mkdir(folder, { recursive: true });
  try {
    await pipeline(Readable.fromWeb(response.body as ReadableStream), createWriteStream(partial));
    if (!(await holds(partial, file))) {
      throw new Error(`${file.url} sent a file other than the one its sha256 names.`);
    }
    await rename(partial, path);
  } finally {
    await rm(partial, { force: true });
  }
  return path;
}

/** Whether the file at `path` is `file`: its size, then its sha256. */
export async function holds(path: string, file: FetchedFile): Promise<boolean> {
  try {
    if ((await stat(path)).size !== file.bytes) return false;
  } catch {
    return false;
  }
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(path)) hash.update(chunk);
  return hash.digest('hex') === file.sha256;
}

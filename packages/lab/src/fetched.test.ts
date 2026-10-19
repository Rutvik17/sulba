import { createHash } from 'node:crypto';
import { mkdtemp, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { createServer, type Server } from 'node:http';
import type { AddressInfo } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterAll, afterEach, beforeAll, expect, test } from 'vitest';
import { fetchedPath, holds } from './fetched.ts';

// A publisher's server, sending each file it has by its path, and keeping each request's path
// and the user agent it named.
const files = new Map<string, Uint8Array>();
const requests: string[] = [];
const agents: string[] = [];
let server: Server;
let address: string;
const folders: string[] = [];

beforeAll(async () => {
  server = createServer((request, response) => {
    requests.push(request.url ?? '');
    agents.push(request.headers['user-agent'] ?? '');
    const body = files.get(request.url ?? '');
    if (!body) {
      response.writeHead(404).end();
      return;
    }
    response.writeHead(200, { 'Content-Length': body.length }).end(body);
  });
  await new Promise<void>((done) => server.listen(0, '127.0.0.1', done));
  address = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
});

afterAll(() => new Promise<void>((done) => server.close(() => done())));

afterEach(async () => {
  files.clear();
  requests.length = 0;
  agents.length = 0;
  for (const folder of folders.splice(0)) await rm(folder, { recursive: true, force: true });
});

/** A new folder for the files, which the test removes. */
async function folder(): Promise<string> {
  const made = await mkdtemp(join(tmpdir(), 'sulba-fetched-'));
  folders.push(made);
  return made;
}

/** `body`, served at `path`, as a lab pins it. */
function served(path: string, body: Uint8Array) {
  files.set(path, body);
  const sha256 = createHash('sha256').update(body).digest('hex');
  return { url: `${address}${path}`, bytes: body.length, sha256 };
}

const tiles = new Uint8Array(4096).map((_, index) => index % 251);

test('a file is fetched once, and kept under its sha256', async () => {
  const kept = await folder();
  const file = served('/tiles.bin', tiles);
  const path = await fetchedPath(file, kept);
  expect(path).toBe(join(kept, file.sha256));
  expect(new Uint8Array(await readFile(path))).toEqual(tiles);
  expect(await fetchedPath(file, kept)).toBe(path);
  expect(requests).toEqual(['/tiles.bin']);
});

test('a fetch names its client, which some publishers require', async () => {
  await fetchedPath(served('/tiles.bin', tiles), await folder());
  expect(agents).toEqual(['sulba']);
});

test('checks that want the same file at once share one fetch', async () => {
  const kept = await folder();
  const file = served('/tiles.bin', tiles);
  const [first, second] = await Promise.all([fetchedPath(file, kept), fetchedPath(file, kept)]);
  expect(second).toBe(first);
  expect(requests).toEqual(['/tiles.bin']);
});

test('a fetch that failed is tried again by the next check that wants the file', async () => {
  const kept = await folder();
  const file = served('/tiles.bin', tiles);
  files.delete('/tiles.bin');
  await expect(fetchedPath(file, kept)).rejects.toThrow('answered 404');
  files.set('/tiles.bin', tiles);
  expect(await holds(await fetchedPath(file, kept), file)).toBe(true);
  expect(requests).toEqual(['/tiles.bin', '/tiles.bin']);
});

test('a kept copy that is not the file its sha256 names is fetched again', async () => {
  const kept = await folder();
  const file = served('/tiles.bin', tiles);
  await writeFile(join(kept, file.sha256), new Uint8Array(tiles.length));
  expect(await holds(join(kept, file.sha256), file)).toBe(false);
  const path = await fetchedPath(file, kept);
  expect(await holds(path, file)).toBe(true);
  expect(requests).toEqual(['/tiles.bin']);
});

test('a publisher that sends another file is refused, and nothing is kept', async () => {
  const kept = await folder();
  const file = { ...served('/tiles.bin', tiles), sha256: '0'.repeat(64) };
  await expect(fetchedPath(file, kept)).rejects.toThrow(
    `${address}/tiles.bin sent a file other than the one its sha256 names.`,
  );
  expect(await readdir(kept)).toEqual([]);
});

test('a publisher that has no such file is refused', async () => {
  const kept = await folder();
  const file = { url: `${address}/gone.bin`, bytes: 1, sha256: '0'.repeat(64) };
  await expect(fetchedPath(file, kept)).rejects.toThrow(`${address}/gone.bin answered 404.`);
});

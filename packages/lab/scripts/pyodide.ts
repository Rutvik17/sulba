// Puts together the Pyodide files Sulba serves from its own domain: Pyodide's core from its npm
// package, and a wheel for each package sessions use, with everything those need. Wheels come
// from Pyodide's CDN once, are checked against the sha256 in Pyodide's lock file, and are kept
// in `pyodide/` for the next run.
import { createHash } from 'node:crypto';
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { pythonPackages } from '../src/protocol.ts';

interface LockPackage {
  readonly file_name: string;
  readonly sha256: string;
  readonly depends: readonly string[];
}

const core = ['pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm', 'python_stdlib.zip'];
// pytest runs every session's tests, so it is always served.
const always = ['pytest'];

const folder = dirname(createRequire(import.meta.url).resolve('pyodide/package.json'));
const out = fileURLToPath(new URL('../pyodide/', import.meta.url));
const lockText = await readFile(join(folder, 'pyodide-lock.json'), 'utf8');
const lock = JSON.parse(lockText) as { packages: Record<string, LockPackage> };
const { version } = JSON.parse(await readFile(join(folder, 'package.json'), 'utf8')) as {
  version: string;
};

/** Every package the named ones need, themselves included. */
function needed(names: readonly string[]): Set<string> {
  const found = new Set<string>();
  const visit = (name: string) => {
    if (found.has(name)) return;
    const entry = lock.packages[name];
    if (!entry) throw new Error(`Pyodide ${version} has no package named ${name}.`);
    found.add(name);
    for (const dependency of entry.depends) visit(dependency);
  };
  for (const name of names) visit(name);
  return found;
}

function sha256(bytes: Uint8Array): string {
  return createHash('sha256').update(bytes).digest('hex');
}

async function kept(path: string, hash: string): Promise<boolean> {
  try {
    return sha256(await readFile(path)) === hash;
  } catch {
    return false;
  }
}

await mkdir(out, { recursive: true });
for (const file of core) await copyFile(join(folder, file), join(out, file));
await writeFile(join(out, 'pyodide-lock.json'), lockText);

for (const name of needed([...always, ...pythonPackages])) {
  const { file_name: file, sha256: hash } = lock.packages[name] as LockPackage;
  const path = join(out, file);
  if (await kept(path, hash)) continue;
  const response = await fetch(`https://cdn.jsdelivr.net/pyodide/v${version}/full/${file}`);
  if (!response.ok) throw new Error(`${file}: ${response.status} ${response.statusText}`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (sha256(bytes) !== hash) throw new Error(`${file} doesn't match Pyodide's lock file.`);
  await writeFile(path, bytes);
}

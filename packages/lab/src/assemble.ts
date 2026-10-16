// Puts together the Pyodide files Sulba serves from its own domain: Pyodide's core from its npm
// package, and a wheel for each package sessions use, with everything those need. Wheels come
// from Pyodide's CDN once, or from PyPI for the few that Pyodide doesn't ship, are checked
// against their sha256, and are kept in `pyodide/` for the next time.
import { createHash } from 'node:crypto';
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { basename, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { pythonPackages } from './protocol.ts';

interface LockPackage {
  readonly name: string;
  readonly version: string;
  readonly file_name: string;
  readonly install_dir: 'site';
  readonly sha256: string;
  readonly package_type: 'package';
  readonly imports: readonly string[];
  readonly depends: readonly string[];
  readonly unvendored_tests: boolean;
  readonly tool: Record<string, never>;
}

/** A pure-Python wheel from PyPI, with the sha256 PyPI gives for it. */
export interface PyPIWheel {
  readonly name: string;
  readonly version: string;
  readonly url: string;
  readonly sha256: string;
  /** The modules it gives, as Pyodide's lock file lists them. */
  readonly imports: readonly string[];
}

/** Wheels from PyPI that a package of Pyodide's needs and Pyodide doesn't ship. */
export const pypiWheels: readonly PyPIWheel[] = [
  {
    name: 'mypy-extensions',
    version: '1.1.0',
    url: 'https://files.pythonhosted.org/packages/79/7b/2c79738432f5c924bef5071f933bcc9efd0473bac3b4aa584a6f7c1c8df8/mypy_extensions-1.1.0-py3-none-any.whl',
    sha256: '1be4cccdb0f2482337c4743e60421de3a356cd97508abadd57d47403e94f5505',
    imports: ['mypy_extensions'],
  },
  {
    name: 'pathspec',
    version: '1.1.1',
    url: 'https://files.pythonhosted.org/packages/f1/d9/7fb5aa316bc299258e68c73ba3bddbc499654a07f151cba08f6153988714/pathspec-1.1.1-py3-none-any.whl',
    sha256: 'a00ce642f577bf7f473932318056212bc4f8bfdf53128c78bbd5af0b9b20b189',
    imports: ['pathspec'],
  },
];

/**
 * Dependencies that Pyodide's lock file leaves out, by package. mypy 1.19.1 requires
 * typing_extensions, mypy_extensions and pathspec, and the lock file lists only librt
 * (decision record 22).
 */
const missing: Readonly<Record<string, readonly string[]>> = {
  mypy: ['typing-extensions', 'mypy-extensions', 'pathspec'],
};

const core = ['pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm', 'python_stdlib.zip'];
// pytest runs every session's tests, so it is always served.
const always = ['pytest'];

/** Where the files are put together. */
export const pyodideFolder = fileURLToPath(new URL('../pyodide/', import.meta.url));

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

/**
 * Pyodide's lock file with the wheels from PyPI added, and the dependencies it leaves out, so
 * Pyodide loads them with the package that needs them.
 */
function completed(lock: { packages: Record<string, LockPackage> }) {
  const packages = { ...lock.packages };
  for (const { name, version, url, sha256, imports } of pypiWheels) {
    packages[name] = {
      name,
      version,
      file_name: basename(url),
      install_dir: 'site',
      sha256,
      package_type: 'package',
      imports,
      depends: [],
      unvendored_tests: false,
      tool: {},
    };
  }
  for (const [name, depends] of Object.entries(missing)) {
    const entry = packages[name];
    if (!entry) throw new Error(`Pyodide's lock file has no package named ${name}.`);
    packages[name] = { ...entry, depends: [...entry.depends, ...depends] };
  }
  return { ...lock, packages };
}

/** Put the files together in `pyodideFolder`, downloading only wheels not already there. */
export async function assemblePyodide(): Promise<void> {
  const source = dirname(createRequire(import.meta.url).resolve('pyodide/package.json'));
  const lock = completed(JSON.parse(await readFile(join(source, 'pyodide-lock.json'), 'utf8')));
  const { version } = JSON.parse(await readFile(join(source, 'package.json'), 'utf8')) as {
    version: string;
  };
  const fromPyPI = new Map(pypiWheels.map(({ url }) => [basename(url), url]));

  // A dependency can name a package as written or as PEP 503 normalizes it, pydantic_core for
  // pydantic-core, and Pyodide matches either.
  const canonical = (name: string) => name.toLowerCase().replace(/[-_.]+/g, '-');
  const named = new Map(Object.keys(lock.packages).map((key) => [canonical(key), key]));
  const needed = new Set<string>();
  const visit = (dependency: string) => {
    const name = named.get(canonical(dependency));
    if (name === undefined)
      throw new Error(`Pyodide ${version} has no package named ${dependency}.`);
    if (needed.has(name)) return;
    needed.add(name);
    for (const each of (lock.packages[name] as LockPackage).depends) visit(each);
  };
  for (const name of [...always, ...pythonPackages]) visit(name);

  await mkdir(pyodideFolder, { recursive: true });
  for (const file of core) await copyFile(join(source, file), join(pyodideFolder, file));
  await writeFile(join(pyodideFolder, 'pyodide-lock.json'), JSON.stringify(lock));

  for (const name of needed) {
    const { file_name: file, sha256: hash } = lock.packages[name] as LockPackage;
    const path = join(pyodideFolder, file);
    if (await kept(path, hash)) continue;
    const url = fromPyPI.get(file) ?? `https://cdn.jsdelivr.net/pyodide/v${version}/full/${file}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${file}: ${response.status} ${response.statusText}`);
    const bytes = new Uint8Array(await response.arrayBuffer());
    if (sha256(bytes) !== hash) throw new Error(`${file} doesn't match its sha256.`);
    await writeFile(path, bytes);
  }
}

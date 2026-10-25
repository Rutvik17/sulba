// Runs each lab that runs on the learner's machine from its download, as a learner would there
// (decision record 28), so that CI can run it on Windows, macOS and Linux: each stage's starter
// fails and its solution passes through `uv run sulba.py`, `uv run sulba.py next` opens the next
// stage, a lab with TypeScript for the browser builds it with `uv run sulba.py build`, and a lab
// with a Dockerfile builds its image where Docker runs Linux containers. The runner fetches the
// lab's files from their publishers (decision record 29), all but those kept from an earlier run,
// and keeps the ones it fetched for the next. With `--figures <file>`, each stage's figures,
// computed in the download's own environment, go to that file, whose text must then be the same on
// every system. With `--lab <path>`, it runs only the lab at that path in its folder of courses,
// such as `ai-engineering/modules/pytorch/labs/transfer-learning`, so that CI can run each lab in a
// job of its own. With `--every-file`, it then fetches each file a machine lab pins that isn't kept
// yet, so that one job's folder holds them all for CI to keep. With `--model`, it runs no stages:
// from a download of each lab that serves a model no lab before it serves,
// `uv run sulba.py model --check` fetches llama.cpp's server for this system and the lab's models,
// starts them and asks each one thing (decision record 34).
//
//   node scripts/machine.ts <folder of courses>... [--lab <path>] [--every-file] [--figures <file>]
//   node scripts/machine.ts <folder of courses>... --model
import { spawnSync } from 'node:child_process';
import { copyFile, mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { fetchedFolder, fetchedPath, holds } from '@sulba/lab/fetched';
import { machineDownload } from '@sulba/lab/machine';
import { figuresInCPython, runnerFiles } from '@sulba/lab/node';
import type { FetchedFile } from '@sulba/lab/protocol';
import {
  courseSlugs,
  fetchedFiles,
  figuresFiles,
  labFiles,
  loadCourse,
  machineLabOf,
  machineLabs,
  type Problem,
} from '../src/index.ts';

const { positionals, values } = parseArgs({
  allowPositionals: true,
  options: {
    figures: { type: 'string' },
    lab: { type: 'string' },
    'every-file': { type: 'boolean', default: false },
    model: { type: 'boolean', default: false },
  },
});
const runner = await runnerFiles();
const problems: Problem[] = [];
const figures: Record<string, Record<string, string> | null> = {};
/** Each file a machine lab pins, with the lab's path. */
const pinned: { path: string; file: FetchedFile }[] = [];
/** The sha256 of each model checked, so a model several labs serve is checked once. */
const served = new Set<string>();
let ran = 0;

/** `uv run sulba.py` with these arguments in the download's folder, and its exit code. */
function sulba(folder: string, ...args: string[]): { code: number | null; output: string } {
  const ran = spawnSync('uv', ['run', 'sulba.py', ...args], { cwd: folder, encoding: 'utf8' });
  return { code: ran.status, output: `${ran.stdout}${ran.stderr}` };
}

/** Whether Docker is here and runs Linux containers. */
function dockerOnLinux(): boolean {
  const version = spawnSync('docker', ['version', '--format', '{{.Server.Os}}'], {
    encoding: 'utf8',
  });
  return version.status === 0 && version.stdout.trim() === 'linux';
}

for (const root of positionals.map((each) => resolve(each))) {
  const courses = [];
  for (const slug of await courseSlugs(root)) {
    const loaded = await loadCourse(root, slug);
    problems.push(...loaded.problems);
    if (loaded.course) courses.push(loaded.course);
  }
  for (const { lab, path } of machineLabs(root, courses)) {
    pinned.push(...Object.values(fetchedFiles(lab)).map((file) => ({ path, file })));
    if (values.lab !== undefined && path !== values.lab) continue;
    if (values.model && lab.models.every((model) => served.has(model.file.sha256))) continue;
    ran += 1;
    const problem = (message: string) => problems.push({ path, message });
    const folder = join(await mkdtemp(join(tmpdir(), 'sulba-machine-')), lab.slug);
    const [first] = lab.stages;
    if (!first) continue;
    const download = machineDownload({
      project: { ...lab.project, ...runner },
      data: labFiles(lab),
      files: { [first.file]: first.starter },
      lab: machineLabOf(lab, `https://sulba.dev/${path}/`, 0),
    });
    for (const [name, text] of Object.entries(download)) {
      await mkdir(dirname(join(folder, name)), { recursive: true });
      await writeFile(join(folder, name), text);
    }
    if (values.model) {
      for (const model of lab.models) served.add(model.file.sha256);
      const asked = sulba(folder, 'model', '--check');
      const titles = lab.models.map((model) => model.title).join(', ');
      if (asked.code !== 0) problem(`its models should answer.\n${asked.output}`);
      else console.log(`${path}: ${titles} answered from the download.`);
      await rm(dirname(folder), { recursive: true, force: true, maxRetries: 3 });
      continue;
    }
    const fetched = fetchedFiles(lab);
    const unkept: string[] = [];
    for (const [name, file] of Object.entries(fetched)) {
      const kept = join(fetchedFolder, file.sha256);
      if (!(await holds(kept, file))) {
        unkept.push(name);
        continue;
      }
      await mkdir(dirname(join(folder, name)), { recursive: true });
      await copyFile(kept, join(folder, name));
    }
    for (const [index, stage] of lab.stages.entries()) {
      const at = `stage ${index + 1}, ${stage.slug}`;
      const starter = sulba(folder);
      if (starter.code !== 1) problem(`${at}: its starter should fail.\n${starter.output}`);
      await writeFile(join(folder, stage.file), stage.solution);
      const solved = sulba(folder);
      if (solved.code !== 0) problem(`${at}: its solution should pass.\n${solved.output}`);
      if (index + 1 < lab.stages.length) {
        const next = sulba(folder, 'next');
        if (next.code !== 0) problem(`${at}: next should open the next stage.\n${next.output}`);
      }
    }
    // The page a lab builds for the browser compiles from the stages' solutions.
    if (Object.hasOwn(lab.project, 'tsconfig.build.json')) {
      const built = sulba(folder, 'build');
      if (built.code !== 0) problem(`its build should compile.\n${built.output}`);
    }
    // A lab's Dockerfile builds its image from the stages' solutions, where Docker runs Linux
    // containers.
    if (lab.stages.some((stage) => stage.file === 'Dockerfile') && dockerOnLinux()) {
      const tag = `sulba-check/${lab.slug}`;
      const built = spawnSync('docker', ['build', '--tag', tag, '.'], {
        cwd: folder,
        encoding: 'utf8',
      });
      if (built.status !== 0)
        problem(`its Dockerfile should build.\n${built.stdout}${built.stderr}`);
      spawnSync('docker', ['image', 'rm', '--force', tag]);
    }
    for (const name of unkept) {
      const file = fetched[name];
      if (!file || !(await holds(join(folder, name), file))) continue;
      await mkdir(fetchedFolder, { recursive: true });
      await copyFile(join(folder, name), join(fetchedFolder, file.sha256));
    }
    const withFigures = lab.stages.filter((stage) => stage.figures !== null);
    // A file that can't be fetched leaves the figures uncomputed, and a problem.
    const computed = await figuresInCPython(
      withFigures.map((stage) => figuresFiles(lab, stage)),
      { folder, fetched },
    ).catch((error: Error) => {
      problem(`its figures: ${error.message}`);
      return [];
    });
    withFigures.forEach((stage, index) => {
      const answer = computed[index];
      if (answer?.problem) problem(`${stage.slug}'s figures: ${answer.problem}`);
      figures[`${path}/stages/${stage.slug}`] = answer?.figures ?? null;
    });
    // The download holds copies of the files the lab fetches, which can be large.
    await rm(dirname(folder), { recursive: true, force: true, maxRetries: 3 });
    console.log(`${path}: ${lab.stages.length} stages run from the download.`);
  }
}

if (values.lab !== undefined && ran === 0) {
  problems.push({
    path: values.lab,
    message: values.model
      ? 'No lab that serves a model is here.'
      : "No lab that runs on the learner's machine is here.",
  });
}
if (values['every-file']) {
  for (const { path, file } of pinned) {
    await fetchedPath(file).catch((error: Error) =>
      problems.push({ path, message: error.message }),
    );
  }
}
if (values.figures) await writeFile(values.figures, `${JSON.stringify(figures, null, 2)}\n`);
for (const { path, message } of problems) console.error(`${path}: ${message}`);
console.log(`${Object.keys(figures).length} stages' figures, ${problems.length} problems.`);
process.exitCode = problems.length ? 1 : 0;

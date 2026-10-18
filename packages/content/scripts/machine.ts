// Runs each lab that runs on the learner's machine from its download, as a learner would there
// (decision record 28), so that CI can run it on Windows, macOS and Linux: each stage's starter
// fails and its solution passes through `uv run sulba.py`, and `uv run sulba.py next` opens the
// next stage. With `--figures <file>`, each stage's figures, computed in the download's own
// environment, go to that file, whose text must then be the same on every system.
//
//   node scripts/machine.ts <folder of courses>... [--figures <file>]
import { spawnSync } from 'node:child_process';
import { mkdir, mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { machineDownload } from '@sulba/lab/machine';
import { figuresInCPython, runnerFiles } from '@sulba/lab/node';
import {
  courseSlugs,
  figuresFiles,
  labFiles,
  loadCourse,
  machineLabOf,
  machineLabs,
  type Problem,
} from '../src/index.ts';

const { positionals, values } = parseArgs({
  allowPositionals: true,
  options: { figures: { type: 'string' } },
});
const runner = await runnerFiles();
const problems: Problem[] = [];
const figures: Record<string, Record<string, string> | null> = {};

/** `uv run sulba.py` with these arguments in the download's folder, and its exit code. */
function sulba(folder: string, ...args: string[]): { code: number | null; output: string } {
  const ran = spawnSync('uv', ['run', 'sulba.py', ...args], { cwd: folder, encoding: 'utf8' });
  return { code: ran.status, output: `${ran.stdout}${ran.stderr}` };
}

for (const root of positionals.map((each) => resolve(each))) {
  const courses = [];
  for (const slug of await courseSlugs(root)) {
    const loaded = await loadCourse(root, slug);
    problems.push(...loaded.problems);
    if (loaded.course) courses.push(loaded.course);
  }
  for (const { lab, path } of machineLabs(root, courses)) {
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
    const withFigures = lab.stages.filter((stage) => stage.figures !== null);
    const computed = await figuresInCPython(
      withFigures.map((stage) => figuresFiles(lab, stage)),
      folder,
    );
    withFigures.forEach((stage, index) => {
      const answer = computed[index];
      if (answer?.problem) problem(`${stage.slug}'s figures: ${answer.problem}`);
      figures[`${path}/stages/${stage.slug}`] = answer?.figures ?? null;
    });
    console.log(`${path}: ${lab.stages.length} stages run from the download.`);
  }
}

if (values.figures) await writeFile(values.figures, `${JSON.stringify(figures, null, 2)}\n`);
for (const { path, message } of problems) console.error(`${path}: ${message}`);
console.log(`${Object.keys(figures).length} stages' figures, ${problems.length} problems.`);
process.exitCode = problems.length ? 1 : 0;

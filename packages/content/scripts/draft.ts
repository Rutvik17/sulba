// Drafts problems for a Catch stage with a code model that llama.cpp's llama-server runs on this
// machine, and writes the drafts it keeps to the stage's .drafts.yaml (courses/README.md).
//
//   pnpm --filter @sulba/content draft <stage folder> [--server <url>] [--rounds 3] [--count 8]
import { writeFile } from 'node:fs/promises';
import { basename, join, resolve, sep } from 'node:path';
import { parseArgs } from 'node:util';
import { runEachInCPython } from '@sulba/lab/node';
import { stringify } from 'yaml';
import {
  type Check,
  type Draft,
  type Edit,
  judge,
  messagesOf,
  parseReply,
  replySchema,
  withBug,
} from '../src/draft.ts';
import { checkIds, loadCourse, stageRuns } from '../src/index.ts';

// Long enough for CPython to start and run a stage's tests; a bug that loops forever stops here.
const limitMs = 60_000;

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    server: { type: 'string', default: 'http://127.0.0.1:8080' },
    rounds: { type: 'string', default: '3' },
    count: { type: 'string', default: '8' },
  },
});

function fail(message: string): never {
  console.error(message);
  process.exit(1);
}

// <courses>/<course>/modules/<module>/labs/<lab>/stages/<stage>
const folder = resolve(positionals[0] ?? fail("Name the Catch stage's folder."));
const parts = folder.split(sep);
const [course, modules, module, labs, lab, stages, stage] = parts.slice(-7);
if (modules !== 'modules' || labs !== 'labs' || stages !== 'stages' || !course) {
  fail(`${folder} isn't a stage's folder: <course>/modules/<module>/labs/<lab>/stages/<stage>.`);
}
const loaded = await loadCourse(parts.slice(0, -7).join(sep), course);
const found = loaded.course?.levels
  .flatMap((level) => level.modules)
  .find((each) => each.slug === module)
  ?.labs.find((each) => each.slug === lab);
const index = found?.stages.findIndex((each) => each.slug === stage) ?? -1;
const runs = found && index >= 0 ? stageRuns(found)[index] : undefined;
if (!runs) {
  for (const { path, message } of loaded.problems) console.error(`${path}: ${message}`);
  fail(`${folder} didn't load.`);
}
if (runs.stage.kind !== 'catch') fail(`${runs.stage.title} is a ${runs.stage.kind} stage.`);

/** The run of the stage's solution with its file swapped for `code`. */
const withCode = (code: string) => ({
  ...runs.solution,
  files: { ...runs.solution.files, [runs.stage.file]: code },
});

// The solution passes every test and check, and its run names each check.
const ids = new Set(checkIds(runs.stage.checks).keys());
const [solved] = await runEachInCPython([runs.solution], limitMs);
if (solved?.status !== 'pass') fail("The solution doesn't pass its tests and checks.");
const checks: Check[] = solved.tests.flatMap((test) =>
  test.id && ids.has(test.id) ? [{ id: test.id, name: test.name }] : [],
);

const ask = async (): Promise<{ model: string; drafts: Draft[] }> => {
  const response = await fetch(new URL('/v1/chat/completions', values.server), {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      messages: messagesOf(runs.stage, checks, Number(values.count)),
      temperature: 0.8,
      max_tokens: 4096,
      response_format: {
        type: 'json_schema',
        json_schema: { name: 'drafts', schema: replySchema(checks) },
      },
    }),
  }).catch(() =>
    fail(`No model server at ${values.server}. Start llama-server (courses/README.md).`),
  );
  if (!response.ok) fail(`The model server answered ${response.status}: ${await response.text()}`);
  const body = (await response.json()) as {
    model: string;
    choices: { message: { content: string } }[];
  };
  const content = body.choices[0]?.message.content ?? '';
  try {
    return { model: body.model, drafts: parseReply(content) };
  } catch {
    console.error('A reply was not the JSON asked for, and is skipped.');
    return { model: body.model, drafts: [] };
  }
};

let model = '';
const drafts = new Map<string, Draft>();
for (let round = 1; round <= Number(values.rounds); round++) {
  const answer = await ask();
  model = answer.model;
  for (const draft of answer.drafts) drafts.set(`${draft.line}\u0000${draft.bug.trim()}`, draft);
  console.log(`Round ${round}: ${answer.drafts.length} drafts.`);
}

const rejected = new Map<string, number>();
const reject = (reason: string) => rejected.set(reason, (rejected.get(reason) ?? 0) + 1);
const candidates: { draft: Draft; code: string; edit: Edit }[] = [];
for (const draft of drafts.values()) {
  const edited = withBug(runs.stage.solution, draft);
  if ('reason' in edited) reject(edited.reason);
  else candidates.push({ draft, ...edited });
}
const results = await runEachInCPython(
  candidates.map(({ code }) => withCode(code)),
  limitMs,
);
const kept = candidates.flatMap(({ draft, edit }, at) => {
  const result = results[at];
  const verdict = result ? judge(result, ids) : { kept: false as const, reason: 'No result.' };
  if (!verdict.kept) {
    reject(verdict.reason);
    return [];
  }
  return [{ check: verdict.check, draft, edit }];
});

const drafted = checks.flatMap((check) => {
  const each = kept.filter((entry) => entry.check === check.id);
  return each.length === 0
    ? []
    : [
        {
          check: check.id,
          name: check.name,
          drafts: each.map(({ draft, edit }) => ({
            kind: draft.kind,
            summary: draft.summary,
            edit,
          })),
        },
      ];
});
const out = join(folder, '.drafts.yaml');
await writeFile(
  out,
  `# Drafts by ${basename(model)} on ${new Date().toISOString().slice(0, 10)}, each kept because the\n` +
    "# assistant's tests pass with it and only its check fails. Review each before it becomes a\n" +
    '# problem in stage.yaml, with its bug in the starter.\n' +
    stringify({ checks: drafted, rejected: Object.fromEntries(rejected) }, { lineWidth: 0 }),
);
console.log(
  `${drafts.size} drafts: ${kept.length} kept, for ${drafted.length} of ${checks.length} checks. Written to ${out}.`,
);

// Drafts a Catch stage's problems (courses/README.md). A code model on the author's machine writes
// bugs into the stage's solution, of the kinds in faults.ts, and a draft is kept only when the
// assistant's tests still pass with it and exactly one hidden check fails, as a Catch problem
// must. An author reviews every draft before it becomes a problem.
import type { RunResult } from '@sulba/lab/protocol';
import { z } from 'zod';
import { faults } from './faults.ts';
import type { Stage } from './load.ts';

/** A bug the model wrote: a line of the solution, and what the assistant wrote there instead. */
export interface Draft {
  /** The id of the check the model meant it to fail. */
  readonly check: string;
  /** Its kind, from faults.ts. */
  readonly kind: string;
  /** Counted from 1. */
  readonly line: number;
  /** One line or more, in place of that line. */
  readonly bug: string;
  /** What goes wrong when the code is used. */
  readonly summary: string;
}

/** A Catch problem's edit: the bug as it stands in the starter, and the code that fixes it. */
export interface Edit {
  readonly replace: string;
  readonly with: string;
}

/** A hidden check: its id, and its name as a run shows it. */
export interface Check {
  readonly id: string;
  readonly name: string;
}

export type Verdict =
  | { readonly kept: true; readonly check: string }
  | { readonly kept: false; readonly reason: string };

export interface Message {
  readonly role: 'system' | 'user';
  readonly content: string;
}

/** What a reply must be: JSON that llama-server holds the model to. */
export function replySchema(checks: readonly Check[]) {
  return {
    type: 'object',
    properties: {
      drafts: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            check: { type: 'string', enum: checks.map((check) => check.id) },
            kind: { type: 'string', enum: faults.map((fault) => fault.id) },
            line: { type: 'integer', minimum: 1 },
            bug: { type: 'string' },
            summary: { type: 'string' },
          },
          required: ['check', 'kind', 'line', 'bug', 'summary'],
        },
      },
    },
    required: ['drafts'],
  };
}

const reply = z.object({
  drafts: z.array(
    z.object({
      check: z.string(),
      kind: z.string(),
      line: z.int().min(1),
      bug: z.string(),
      summary: z.string(),
    }),
  ),
});

export function parseReply(content: string): Draft[] {
  return reply.parse(JSON.parse(content)).drafts;
}

/** The conversation that asks for `count` drafts. */
export function messagesOf(stage: Stage, checks: readonly Check[], count: number): Message[] {
  const fence = (code: string) => `\`\`\`python\n${code.trimEnd()}\n\`\`\``;
  const tests = Object.values(stage.tests).map(fence).join('\n\n');
  const numbered = stage.solution
    .trimEnd()
    .split('\n')
    .map((text, at) => `${String(at + 1).padStart(3)} | ${text}`)
    .join('\n');
  return [
    {
      role: 'system',
      content:
        "You plant bugs in correct Python code for a code-review exercise. Each bug is one an AI coding assistant could plausibly write: the code still looks reasonable and still passes the assistant's own tests, but it fails when the code is really used. Reply only with JSON.",
    },
    {
      role: 'user',
      content: [
        `The task the assistant was given:\n\n${stage.brief.trim()}`,
        `The correct code, ${stage.file}, with its lines numbered:\n\n\`\`\`\n${numbered}\n\`\`\``,
        `The assistant's tests. They must all still pass with your bug in place:\n\n${tests}`,
        `How the code is really used. Each line is a check, and a bug must make exactly one of them fail:\n\n${checks.map((check) => `- ${check.id}: ${check.name}`).join('\n')}`,
        `Kinds of bug to draw on:\n\n${faults.map((fault) => `- ${fault.id}: ${fault.description}`).join('\n')}`,
        [
          `Write ${count} different bugs, spread across the checks. For each, give:`,
          '- check: the id of the check it makes fail',
          '- kind: one of the kinds above',
          '- line: the number of the line the bug changes',
          '- bug: what the assistant wrote on that line instead, one line or more, without its number',
          '- summary: one sentence on what goes wrong when the code is used',
        ].join('\n'),
      ].join('\n\n'),
    },
  ];
}

/**
 * The stage's file with the draft's bug on its line, and the edit that fixes it, or why it can't
 * be a problem. A bug written without the line's indent takes it. The edit leaves out the indent,
 * and a Catch problem's edit finds its bug once in the starter, so the bug must appear only once.
 */
export function withBug(
  solution: string,
  draft: Draft,
): { code: string; edit: Edit } | { reason: string } {
  const lines = solution.split('\n');
  const original = lines[draft.line - 1];
  if (original === undefined || original.trim() === '') {
    return { reason: 'Its line has no code.' };
  }
  // A fix that puts back a comment would read as no fix at all.
  if (original.trim().startsWith('#')) return { reason: 'Its line is a comment.' };
  const indent = /^\s*/.exec(original)?.[0] ?? '';
  const written = draft.bug.replace(/\n+$/, '').split('\n');
  const bug = /^\s/.test(written[0] ?? '') ? written : written.map((each) => indent + each);
  const edit = { replace: bug.join('\n').trim(), with: original.trim() };
  if (edit.replace === edit.with) return { reason: 'It changes nothing.' };
  const code = [...lines.slice(0, draft.line - 1), ...bug, ...lines.slice(draft.line)].join('\n');
  const found = code.split(edit.replace).length - 1;
  if (found !== 1) return { reason: `Its bug would appear ${found} times in the starter.` };
  return { code, edit };
}

/** Whether a run with the bug keeps it: the assistant's tests pass and exactly one check fails. */
export function judge(result: RunResult, checks: ReadonlySet<string>): Verdict {
  if (result.problem) return { kept: false, reason: `It doesn't run: ${result.problem.kind}.` };
  const failing = result.tests.filter((test) => test.status !== 'pass');
  if (failing.some((test) => !test.id || !checks.has(test.id))) {
    return { kept: false, reason: "The assistant's tests catch it." };
  }
  const [only, ...more] = failing;
  if (!only?.id) return { kept: false, reason: 'No check catches it.' };
  if (more.length > 0) return { kept: false, reason: `${failing.length} checks catch it.` };
  return { kept: true, check: only.id };
}

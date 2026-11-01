// Releases: a request delivered once every spec drafted from it is approved and every one of their
// criteria is proven, approved by a person (decision record 62). A release keeps what was proven
// when it was approved, and its document is written from that.
import type { Client } from './client.ts';
import type { CriterionProof } from './evidence.ts';
import { refusal } from './refusal.ts';
import type { Request } from './requests.ts';
import { type SpecStatus, statusNames } from './specs.ts';
import { type TaskRole, type TaskStatus, taskRoleNames, taskStatusNames } from './tasks.ts';

/** A spec as a release keeps it. */
export interface ReleasedSpec {
  readonly number: number;
  readonly title: string;
  readonly status: SpecStatus;
  readonly criteria: readonly {
    readonly number: number;
    readonly text: string;
    /** How many tests proved it. */
    readonly tests: number;
  }[];
  readonly tasks: readonly {
    readonly number: number;
    readonly title: string;
    readonly role: TaskRole;
    readonly status: TaskStatus;
    readonly pullRequest: string | null;
  }[];
}

export interface Release {
  readonly id: string;
  readonly number: number;
  readonly note: string | null;
  readonly approvedBy: string | null;
  readonly approvedAt: string;
  readonly specs: readonly ReleasedSpec[];
}

/** What a snapshot holds, as Postgres writes it. */
type Snapshot = {
  number: number;
  title: string;
  status: SpecStatus;
  criteria: { number: number; text: string; tests: number }[];
  tasks: {
    number: number;
    title: string;
    role: TaskRole;
    status: TaskStatus;
    pull_request: string | null;
  }[];
}[];

/** A request's releases, the newest first. */
export async function releasesOf(client: Client, requestId: string): Promise<Release[]> {
  const { data, error } = await client
    .from('releases')
    .select('id, number, note, approved_by, approved_at, snapshot')
    .eq('request_id', requestId)
    .order('number', { ascending: false });
  if (error) throw refusal(error);
  return data.map((row) => ({
    id: row.id,
    number: row.number,
    note: row.note,
    approvedBy: row.approved_by,
    approvedAt: row.approved_at,
    specs: (row.snapshot as Snapshot).map((spec) => ({
      number: spec.number,
      title: spec.title,
      status: spec.status,
      criteria: spec.criteria,
      tasks: spec.tasks.map(({ pull_request, ...task }) => ({
        ...task,
        pullRequest: pull_request,
      })),
    })),
  }));
}

/** Approves a release of the request, and gives its number. */
export async function approveRelease(
  client: Client,
  requestId: string,
  note: string,
): Promise<number> {
  const { data, error } = await client.rpc('approve_release', {
    request: requestId,
    ...(note.trim() ? { note: note.trim() } : {}),
  });
  if (error) throw refusal(error);
  return data;
}

/** What still stands between a request and its release, as Postgres checks it; empty when ready. */
export function releaseBlockers(
  specs: readonly { readonly number: number; readonly status: SpecStatus }[],
  proofs: readonly CriterionProof[],
): string[] {
  const counted = specs.filter(
    (spec) => spec.status !== 'abandoned' && spec.status !== 'superseded',
  );
  if (counted.length === 0) return ['Draft at least one spec from it.'];
  return counted.flatMap((spec) => {
    const key = `SPEC-${spec.number}`;
    if (spec.status === 'draft' || spec.status === 'in_review') {
      return [`${key} is ${statusNames[spec.status].toLowerCase()}, not approved.`];
    }
    const criteria = proofs.filter((proof) => proof.specNumber === spec.number);
    if (criteria.length === 0) return [`${key} has no criteria.`];
    const unproven = criteria.filter((proof) => proof.state !== 'proven');
    if (unproven.length === 0) return [];
    const ids = unproven.map((proof) => `AC-${proof.criterionNumber}`).join(', ');
    return [`${key} has ${unproven.length} of ${criteria.length} criteria not proven yet: ${ids}.`];
  });
}

const day = new Intl.DateTimeFormat('en-US', { dateStyle: 'long', timeZone: 'UTC' });

/** A table cell's text, with its pipes escaped and its lines joined. */
function cell(text: string): string {
  return text.replaceAll('|', '\\|').replaceAll('\n', ' ');
}

/**
 * The release's document, in Markdown: what was asked, the questions answered about it, and each
 * spec with the tests that proved each criterion and the pull requests that built it.
 */
export function releaseDocument(
  request: Pick<Request, 'number' | 'title' | 'body' | 'questions'>,
  release: Release,
  approver: string,
): string {
  const key = `REQ-${request.number}`;
  const answered = request.questions.filter((question) => question.answer !== null);
  const lines = [
    `# ${key} ${request.title}: release ${release.number}`,
    '',
    `Approved by ${approver} on ${day.format(new Date(release.approvedAt))} (UTC).`,
    ...(release.note ? ['', `> ${release.note.replaceAll('\n', '\n> ')}`] : []),
    '',
    '## What was asked',
    '',
    request.body.trim() || 'Nothing beyond its title.',
  ];
  if (answered.length) {
    lines.push('', '## Questions answered', '');
    for (const question of answered) {
      lines.push(`- **${question.text}**`, `  ${question.answer?.replaceAll('\n', '\n  ')}`);
    }
  }
  lines.push('', '## What was built');
  for (const spec of release.specs) {
    lines.push(
      '',
      `### SPEC-${spec.number} ${spec.title}`,
      '',
      `${statusNames[spec.status]}. Every criterion was proven by the tests that name it when the release was approved.`,
      '',
      '| Criterion | Proven by |',
      '| --- | --- |',
      ...spec.criteria.map(
        (criterion) =>
          `| AC-${criterion.number} ${cell(criterion.text)} | ${criterion.tests} ${criterion.tests === 1 ? 'test' : 'tests'} |`,
      ),
    );
    if (spec.tasks.length) {
      lines.push('', 'Tasks:', '');
      for (const task of spec.tasks) {
        const where = task.pullRequest ? `, ${task.pullRequest}` : '';
        lines.push(
          `- TASK-${task.number} ${task.title} (${taskRoleNames[task.role]}; ${taskStatusNames[task.status]}${where})`,
        );
      }
    }
  }
  return `${lines.join('\n')}\n`;
}

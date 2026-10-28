/*
  The tools Sulba's MCP server gives a coding agent (decision record 51). Each one acts as the
  agent's person, through row-level security, so an agent reads and writes only what its person
  may, and Postgres keeps the decisions about a spec, and about a workspace, with people. Each
  answers in Markdown, which agents read as it is.
*/
import { type CallToolResult, McpServer } from '@modelcontextprotocol/server';
import type { Client } from '@sulba/data/client';
import {
  type Claim,
  type CriterionProof,
  claimsOfSpec,
  proofsOf,
  proofsOfSpec,
  specProofsOf,
} from '@sulba/data/evidence';
import {
  addCriterion,
  createSpec,
  criterionKey,
  rewordCriterion,
  type Spec,
  type SpecStatus,
  specAt,
  specKey,
  specNumberOf,
  specsOf,
  statusNames,
  updateSpec,
} from '@sulba/data/specs';
import { type Workspace, workspaceAt, workspacesOf } from '@sulba/data/workspaces';
import { z } from 'zod';

export interface Agent {
  readonly client: Client;
  readonly personId: string;
  /** The site's address, for links to the app's pages. */
  readonly origin: string;
}

export const instructions = [
  'Sulba holds the team’s specs: what to build, and the numbered acceptance criteria that say when it’s done.',
  'Before building, read the spec with get_spec, and build what its criteria say.',
  'A test proves a criterion by putting the criterion’s ID in its name, such as test_SPEC_12_AC_3_retries_once for SPEC-12/AC-3. When the team’s CI runs it on the repository’s branch, Sulba marks the criterion proven or failing.',
  'You can draft specs, add and reword criteria, put a spec in review and mark it implemented. People approve, abandon and supersede specs.',
].join(' ');

const workspaceInput = z
  .string()
  .describe(
    'The workspace’s address, such as acme for sulba.dev/app/acme. list_workspaces gives them.',
  );
const specInput = z.string().describe('The spec’s ID, such as SPEC-12.');

const answer = (text: string): CallToolResult => ({ content: [{ type: 'text', text }] });

/** Runs a tool's work and answers with what it says, or with why it couldn't be done. */
async function run(work: () => Promise<string>): Promise<CallToolResult> {
  try {
    return answer(await work());
  } catch (error) {
    const said = error instanceof Error ? error.message : 'Sulba couldn’t do that just now.';
    return { content: [{ type: 'text', text: said }], isError: true };
  }
}

async function workspaceOf(agent: Agent, slug: string): Promise<Workspace> {
  const workspace = await workspaceAt(agent.client, agent.personId, slug.trim().toLowerCase());
  if (!workspace) {
    throw new Error(
      `You aren’t in a workspace at ${slug}. list_workspaces gives the ones you’re in.`,
    );
  }
  return workspace;
}

async function specOf(agent: Agent, workspace: Workspace, id: string): Promise<Spec> {
  const number = specNumberOf(id.trim());
  if (number === null) throw new Error(`${id} isn’t a spec’s ID. One looks like SPEC-12.`);
  const spec = await specAt(agent.client, workspace.id, number);
  if (!spec) throw new Error(`${workspace.name} has no ${specKey(number)}.`);
  return spec;
}

/** The spec and criterion numbers in an ID such as SPEC-12/AC-3. */
function criterionNumbers(id: string): { spec: number; criterion: number } {
  const match = /^SPEC-([1-9]\d{0,8})\/AC-([1-9]\d{0,8})$/i.exec(id.trim());
  if (!match) throw new Error(`${id} isn’t a criterion’s ID. One looks like SPEC-12/AC-3.`);
  return { spec: Number(match[1]), criterion: Number(match[2]) };
}

const count = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;

/** A criterion's proof, as a phrase. */
export function proofText(proof: CriterionProof | undefined): string {
  if (!proof || proof.tests === 0) return 'Unproven: no test names it yet';
  if (proof.state === 'failing') {
    return `Failing: ${proof.failed} of ${count(proof.tests, 'test', 'tests')} failed`;
  }
  if (proof.state === 'proven') return `Proven by ${count(proof.tests, 'test', 'tests')}`;
  if (proof.suspectSince) {
    return 'Unproven: reworded since its tests ran, until a person confirms they check the new wording';
  }
  return `Unproven: ${count(proof.skipped, 'test was', 'tests were')} skipped`;
}

/** The lines that list a spec's criteria, each with its proof and what its failing tests said. */
export function criteriaText(
  spec: Spec,
  proofs: readonly CriterionProof[],
  claims: readonly Claim[],
): string[] {
  if (spec.criteria.length === 0) return ['No criteria yet.'];
  return spec.criteria.flatMap((criterion) => {
    const id = criterionKey(spec.number, criterion.number);
    const proof = proofs.find((each) => each.criterionNumber === criterion.number);
    const failures = claims
      .filter((claim) => claim.criterionNumber === criterion.number && claim.outcome === 'failed')
      .map(
        (claim) =>
          `  - ${claim.name} failed in ${claim.repository} at ${claim.sha.slice(0, 7)}${claim.message ? `: ${claim.message}` : ''}`,
      );
    return [`- ${id}: ${criterion.text} (${proofText(proof)})`, ...failures];
  });
}

/** Sulba's MCP server for one agent's request, its tools acting as the agent's person. */
export function createServer(agent: Agent): McpServer {
  const server = new McpServer(
    { name: 'sulba', title: 'Sulba', version: '1.0.0' },
    { instructions },
  );
  const read = { readOnlyHint: true, openWorldHint: false } as const;
  const write = { readOnlyHint: false, destructiveHint: false, openWorldHint: false } as const;
  const link = (workspace: Workspace, path: string) =>
    `${agent.origin}/app/${workspace.slug}/${path}`;

  server.registerTool(
    'list_workspaces',
    {
      title: 'List workspaces',
      description: 'The workspaces you’re in, with your role in each.',
      annotations: read,
    },
    () =>
      run(async () => {
        const workspaces = await workspacesOf(agent.client, agent.personId);
        if (workspaces.length === 0) return 'You aren’t in any workspace yet.';
        return workspaces.map((each) => `- ${each.slug}: ${each.name} (${each.role})`).join('\n');
      }),
  );

  server.registerTool(
    'list_specs',
    {
      title: 'List specs',
      description:
        'Every spec in a workspace, newest first, with its status and how many of its criteria the tests prove.',
      inputSchema: z.object({ workspace: workspaceInput }),
      annotations: read,
    },
    ({ workspace: slug }) =>
      run(async () => {
        const workspace = await workspaceOf(agent, slug);
        const [specs, proofs] = await Promise.all([
          specsOf(agent.client, workspace.id),
          specProofsOf(agent.client, workspace.id),
        ]);
        if (specs.length === 0) return `${workspace.name} has no specs yet.`;
        return specs
          .map((spec) => {
            const proof = proofs.get(spec.id);
            const proven = proof?.criteria
              ? `${proof.proven} of ${count(proof.criteria, 'criterion', 'criteria')} proven${proof.failing ? `, ${proof.failing} failing` : ''}`
              : 'no criteria';
            return `- ${specKey(spec.number)}: ${spec.title} (${statusNames[spec.status]}; ${proven})`;
          })
          .join('\n');
      }),
  );

  server.registerTool(
    'get_spec',
    {
      title: 'Read a spec',
      description:
        'A spec: its status, its text and its acceptance criteria, each with its ID and whether the team’s tests prove it, and what each failing test said. Read it before building what it describes.',
      inputSchema: z.object({ workspace: workspaceInput, spec: specInput }),
      annotations: read,
    },
    ({ workspace: slug, spec: id }) =>
      run(async () => {
        const workspace = await workspaceOf(agent, slug);
        const spec = await specOf(agent, workspace, id);
        const [proofs, claims] = await Promise.all([
          proofsOfSpec(agent.client, workspace.id, spec.id),
          claimsOfSpec(agent.client, workspace.id, spec.number),
        ]);
        return [
          `# ${specKey(spec.number)}: ${spec.title}`,
          '',
          `Status: ${statusNames[spec.status]}. ${link(workspace, specKey(spec.number))}`,
          '',
          spec.body.trim() || 'It has no text yet.',
          '',
          '## Acceptance criteria',
          '',
          ...criteriaText(spec, proofs, claims),
          '',
          `A test proves a criterion by putting its ID in its name, with its parts joined by hyphens, underscores, slashes or spaces, such as test_${specKey(spec.number).replace('-', '_')}_AC_1.`,
        ].join('\n');
      }),
  );

  server.registerTool(
    'create_spec',
    {
      title: 'Write a spec',
      description:
        'Writes a draft spec with a title, its acceptance criteria and, if you give it, its text in Markdown. A person approves it before it’s built.',
      inputSchema: z.object({
        workspace: workspaceInput,
        title: z.string().describe('What the spec is about, in at most 200 characters.'),
        criteria: z
          .array(z.string())
          .min(1)
          .describe(
            'Its acceptance criteria, each one thing that must be true, testable on its own.',
          ),
        text: z.string().optional().describe('Why it’s needed and what it covers, in Markdown.'),
      }),
      annotations: write,
    },
    ({ workspace: slug, title, criteria, text }) =>
      run(async () => {
        const workspace = await workspaceOf(agent, slug);
        const number = await createSpec(agent.client, workspace.id, title, criteria);
        if (text?.trim()) {
          const spec = await specOf(agent, workspace, specKey(number));
          await updateSpec(agent.client, spec.id, { body: text });
        }
        return `Wrote ${specKey(number)} as a draft. ${link(workspace, specKey(number))}`;
      }),
  );

  const agentStatuses = [
    'draft',
    'in_review',
    'implemented',
  ] as const satisfies readonly SpecStatus[];
  server.registerTool(
    'update_spec',
    {
      title: 'Change a spec',
      description:
        'Changes a spec’s title, its text in Markdown, or its status: draft, in_review once it’s ready for the team to agree, or implemented once it’s built and merged. People approve, abandon and supersede specs.',
      inputSchema: z.object({
        workspace: workspaceInput,
        spec: specInput,
        title: z.string().optional(),
        text: z.string().optional().describe('The whole text, which replaces what it says now.'),
        status: z.enum(agentStatuses).optional(),
      }),
      annotations: write,
    },
    ({ workspace: slug, spec: id, title, text, status }) =>
      run(async () => {
        if (title === undefined && text === undefined && status === undefined) {
          throw new Error('Give a title, text or status to change.');
        }
        const workspace = await workspaceOf(agent, slug);
        const spec = await specOf(agent, workspace, id);
        await updateSpec(agent.client, spec.id, {
          ...(title === undefined ? {} : { title }),
          ...(text === undefined ? {} : { body: text }),
          ...(status === undefined ? {} : { status }),
        });
        return `Changed ${specKey(spec.number)}.`;
      }),
  );

  server.registerTool(
    'add_criterion',
    {
      title: 'Add a criterion',
      description:
        'Adds an acceptance criterion at the end of a spec, and gives its ID for tests to name.',
      inputSchema: z.object({
        workspace: workspaceInput,
        spec: specInput,
        text: z.string().describe('One thing that must be true, testable on its own.'),
      }),
      annotations: write,
    },
    ({ workspace: slug, spec: id, text }) =>
      run(async () => {
        const workspace = await workspaceOf(agent, slug);
        const spec = await specOf(agent, workspace, id);
        const number = await addCriterion(agent.client, spec.id, text);
        return `Added ${criterionKey(spec.number, number)}.`;
      }),
  );

  server.registerTool(
    'reword_criterion',
    {
      title: 'Reword a criterion',
      description:
        'Rewords an acceptance criterion. If tests already name it, it’s unproven until a person confirms they check the new wording.',
      inputSchema: z.object({
        workspace: workspaceInput,
        criterion: z.string().describe('The criterion’s ID, such as SPEC-12/AC-3.'),
        text: z.string(),
      }),
      annotations: write,
    },
    ({ workspace: slug, criterion: id, text }) =>
      run(async () => {
        const numbers = criterionNumbers(id);
        const workspace = await workspaceOf(agent, slug);
        const spec = await specOf(agent, workspace, specKey(numbers.spec));
        const criterion = spec.criteria.find((each) => each.number === numbers.criterion);
        if (!criterion) throw new Error(`${specKey(spec.number)} has no AC-${numbers.criterion}.`);
        await rewordCriterion(agent.client, criterion.id, text);
        return `Reworded ${criterionKey(spec.number, criterion.number)}.`;
      }),
  );

  server.registerTool(
    'get_evidence',
    {
      title: 'Read the evidence',
      description:
        'The criteria the tests don’t prove yet, failing first, across the workspace’s specs that aren’t abandoned or superseded.',
      inputSchema: z.object({ workspace: workspaceInput }),
      annotations: read,
    },
    ({ workspace: slug }) =>
      run(async () => {
        const workspace = await workspaceOf(agent, slug);
        const proofs = (await proofsOf(agent.client, workspace.id)).filter(
          (proof) => proof.specStatus !== 'abandoned' && proof.specStatus !== 'superseded',
        );
        if (proofs.length === 0) return `${workspace.name}’s specs have no criteria yet.`;
        const open = proofs
          .filter((proof) => proof.state !== 'proven')
          .sort((a, b) => Number(b.state === 'failing') - Number(a.state === 'failing'));
        if (open.length === 0) return `The tests prove all ${proofs.length} criteria.`;
        return [
          `Not proven yet: ${open.length} of ${count(proofs.length, 'criterion', 'criteria')}.`,
          ...open.map(
            (proof) =>
              `- ${criterionKey(proof.specNumber, proof.criterionNumber)} (${proof.specTitle}): ${proof.text} (${proofText(proof)})`,
          ),
        ].join('\n');
      }),
  );

  return server;
}

import { type Claim, type CriterionProof, confirmCriterion } from '@sulba/data/evidence';
import { requestKey, requestNumberOf } from '@sulba/data/requests';
import type { Review } from '@sulba/data/reviewers';
import {
  addCriterion,
  type Criterion,
  criterionKey,
  criterionProblem,
  removeCriterion,
  rewordCriterion,
  type Spec,
  type SpecChange,
  specKey,
  specNumberOf,
  specStatuses,
  statusMeanings,
  statusNames,
  titleProblem,
  updateSpec,
} from '@sulba/data/specs';
import { taskNumberOf } from '@sulba/data/tasks';
import { holds, type Member } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { Select } from '@sulba/ui/select';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from '@tanstack/react-router';
import { type FormEvent, type KeyboardEvent, useState } from 'react';
import { useAccount } from './account';
import { useCommands } from './commands';
import { EditableTitle, SavedText } from './Editing';
import { whatOf, whoOf } from './history';
import { Notice } from './Notice';
import { ProofMark } from './ProofMark';
import { commitUrl, reasonOf, runUrl } from './proofs';
import {
  keys,
  useHistory,
  useMembers,
  useReviews,
  useSpecAt,
  useSpecEvidence,
  useSpecTasks,
} from './queries';
import { RequestPage } from './RequestPage';
import { Reviewers, YourReview } from './Review';
import { useWorkspace } from './Shell';
import { SpecTasks } from './SpecTasks';
import styles from './spec.module.css';
import { TaskPage } from './TaskPage';
import { useTitle } from './title';
import { When } from './When';

const css = classes(
  styles,
  'spec',
  'head',
  'main',
  'side',
  'crumbs',
  'key',
  'title',
  'heading',
  'section',
  'note',
  'criteria',
  'criterion',
  'id',
  'text',
  'proof',
  'tools',
  'add',
  'facts',
  'history',
  'when',
  'unseen',
  'tests',
  'test',
  'outcome',
  'where',
  'message',
  'suspect',
);

const noOwner = 'none';

/** A spec's page, at its ID: SPEC-12, or a request's or a task's, at its own: REQ-3, TASK-7. */
export function SpecPage() {
  const { spec: key } = useParams({ from: '/$slug/$spec' });
  const request = requestNumberOf(key);
  if (request !== null) return <RequestPage number={request} key={`request-${request}`} />;
  const task = taskNumberOf(key);
  if (task !== null) return <TaskPage number={task} key={`task-${task}`} />;
  const number = specNumberOf(key);
  if (number === null) return <NoSpec>There’s no spec at this address.</NoSpec>;
  return <Loaded number={number} key={number} />;
}

function NoSpec({ children }: { children: string }) {
  const workspace = useWorkspace();
  useTitle('No spec here', workspace.name);
  return (
    <div className={css.main}>
      <h1 className={css.title}>No spec here</h1>
      <p className={css.note}>{children}</p>
      <Link to="/$slug/specs" params={{ slug: workspace.slug }}>
        Go to the specs
      </Link>
    </div>
  );
}

function Loaded({ number }: { number: number }) {
  const workspace = useWorkspace();
  const { data: spec } = useSpecAt(workspace, number);
  const { data: members } = useMembers(workspace);
  if (!spec) return <NoSpec>{`${specKey(number)} hasn’t been written in this workspace.`}</NoSpec>;
  return <Page spec={spec} members={members} />;
}

function Page({ spec, members }: { spec: Spec; members: readonly Member[] }) {
  const workspace = useWorkspace();
  const { client, personId } = useAccount();
  const { data: reviews } = useReviews(spec.id);
  const yours = reviews.find((review) => review.reviewerId === personId);
  const queryClient = useQueryClient();
  const canWrite = holds(workspace.role, 'member');
  const key = specKey(spec.number);
  useTitle(`${key} ${spec.title}`, workspace.name);
  const [failure, setFailure] = useState<string | null>(null);

  const reread = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: keys.spec(workspace.id, spec.number) }),
      queryClient.invalidateQueries({ queryKey: keys.specs(workspace.id) }),
      queryClient.invalidateQueries({ queryKey: keys.history(spec.id) }),
      queryClient.invalidateQueries({ queryKey: keys.proofs(workspace.id) }),
      queryClient.invalidateQueries({ queryKey: keys.reviews(spec.id) }),
      queryClient.invalidateQueries({ queryKey: keys.work(workspace.id) }),
    ]);
  const change = useMutation({
    mutationFn: (patch: SpecChange) => updateSpec(client, spec.id, patch),
    onMutate: () => setFailure(null),
    onSuccess: reread,
    onError: (error) => setFailure(error.message),
  });

  const owners = [
    { id: noOwner, name: 'No owner' },
    ...members.map((member) => ({
      id: member.personId,
      name: member.name || member.email || 'Someone',
    })),
  ];
  const current = (yes: boolean) => (yes ? { note: 'Current' } : {});
  useCommands(
    canWrite
      ? [
          {
            id: 'spec-status',
            label: 'Change status',
            group: key,
            keys: ['s'],
            does: {
              title: 'Change status',
              actions: specStatuses.map((status) => ({
                id: status,
                label: statusNames[status],
                ...current(status === spec.status),
                run: () => change.mutate({ status }),
              })),
            },
          },
          {
            id: 'spec-owner',
            label: 'Change owner',
            group: key,
            keys: ['a'],
            does: {
              title: 'Change owner',
              actions: owners.map((owner) => ({
                id: owner.id,
                label: owner.name,
                ...current(owner.id === (spec.ownerId ?? noOwner)),
                run: () => change.mutate({ ownerId: owner.id === noOwner ? null : owner.id }),
              })),
            },
          },
        ]
      : [],
  );

  return (
    <div className={css.spec}>
      <div className={css.head}>
        <nav aria-label="Breadcrumb" className={css.crumbs}>
          <Link to="/$slug/specs" params={{ slug: workspace.slug }}>
            Specs
          </Link>
          <span aria-hidden="true">/</span>
          <span className={css.key}>{key}</span>
        </nav>

        <EditableTitle
          title={spec.title}
          canWrite={canWrite}
          problemOf={titleProblem}
          onSave={(title) => change.mutate({ title })}
        />
        <Notice text={failure} />
        {yours && spec.status === 'in_review' ? (
          <YourReview spec={spec} review={yours} members={members} />
        ) : null}
      </div>

      <div className={css.main}>
        <section className={css.section} aria-labelledby="text">
          <h2 id="text" className={css.unseen}>
            Text
          </h2>
          <SavedText
            text={spec.body}
            label={`${key}’s text`}
            placeholder="Why this is needed, what it changes, and what it leaves out. Markdown works here."
            canWrite={canWrite}
            save={async (body) => {
              await updateSpec(client, spec.id, { body });
              await queryClient.invalidateQueries({ queryKey: keys.history(spec.id) });
            }}
          />
        </section>

        <Criteria spec={spec} canWrite={canWrite} onChanged={reread} />
        <SpecTasks spec={spec} canWrite={canWrite} />
        <History spec={spec} members={members} reviews={reviews} />
      </div>

      <aside className={css.side} aria-label="Details">
        <dl className={css.facts}>
          <div>
            <dt>Status</dt>
            <dd>
              {canWrite ? (
                <Select
                  label="Status"
                  hideLabel
                  size="small"
                  options={specStatuses.map((id) => ({
                    id,
                    name: statusNames[id],
                    description: statusMeanings[id],
                  }))}
                  value={spec.status}
                  onChange={(status) => change.mutate({ status })}
                  isDisabled={change.isPending}
                />
              ) : (
                statusNames[spec.status]
              )}
            </dd>
          </div>
          <div>
            <dt>Owner</dt>
            <dd>
              {canWrite ? (
                <Select
                  label="Owner"
                  hideLabel
                  size="small"
                  options={owners}
                  value={spec.ownerId ?? noOwner}
                  onChange={(owner) => change.mutate({ ownerId: owner === noOwner ? null : owner })}
                  isDisabled={change.isPending}
                />
              ) : (
                (owners.find((owner) => owner.id === spec.ownerId)?.name ?? 'No owner')
              )}
            </dd>
          </div>
          <div>
            <dt>Reviewers</dt>
            <dd>
              <Reviewers spec={spec} reviews={reviews} members={members} canWrite={canWrite} />
            </dd>
          </div>
          {spec.request ? (
            <div>
              <dt>Request</dt>
              <dd>
                <Link
                  to="/$slug/$spec"
                  params={{ slug: workspace.slug, spec: requestKey(spec.request.number) }}
                >
                  {requestKey(spec.request.number)} {spec.request.title}
                </Link>
              </dd>
            </div>
          ) : null}
          <div>
            <dt>Created</dt>
            <dd>
              <When at={spec.createdAt} day />
            </dd>
          </div>
          <div>
            <dt>Updated</dt>
            <dd>
              <When at={spec.updatedAt} />
            </dd>
          </div>
        </dl>
      </aside>
    </div>
  );
}

/** The spec's acceptance criteria, each with its ID, which members add, reword and remove. */
function Criteria({
  spec,
  canWrite,
  onChanged,
}: {
  spec: Spec;
  canWrite: boolean;
  onChanged: () => Promise<unknown>;
}) {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const [text, setText] = useState('');
  const [checked, setChecked] = useState(false);
  const [removing, setRemoving] = useState<Criterion | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const evidence = useSpecEvidence(workspace, spec.id, spec.number);
  const confirm = useMutation({
    mutationFn: (criterion: Criterion) => confirmCriterion(client, criterion.id),
    onSuccess: onChanged,
  });

  const add = useMutation({
    mutationFn: () => addCriterion(client, spec.id, text),
    onSuccess: async () => {
      setText('');
      setChecked(false);
      await onChanged();
    },
  });
  const remove = useMutation({
    mutationFn: (criterion: Criterion) => removeCriterion(client, criterion.id),
    onSuccess: async () => {
      setRemoving(null);
      await onChanged();
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setChecked(true);
    if (criterionProblem(text)) return;
    add.mutate();
  };
  const copy = async (id: string) => {
    try {
      await navigator.clipboard.writeText(id);
      setCopied(id);
    } catch {
      setCopied(null);
    }
  };
  const count = spec.criteria.length === 1 ? '1 criterion' : `${spec.criteria.length} criteria`;

  return (
    <section className={css.section} aria-labelledby="criteria">
      <h2 id="criteria" className={css.heading}>
        Acceptance criteria <span className={css.note}>{count}</span>
      </h2>
      <p className={css.note}>
        A criterion is unproven until a test that names its ID passes. Put the ID in the test’s
        name, such as <code>test_{criterionKey(spec.number, 1).replace(/\W/g, '_')}_retries</code>.
      </p>
      {spec.criteria.length ? (
        <ol className={css.criteria}>
          {spec.criteria.map((criterion) => {
            const id = criterionKey(spec.number, criterion.number);
            const proof = evidence.proofs.data?.find((each) => each.criterionId === criterion.id);
            const claims = (evidence.claims.data ?? []).filter(
              (claim) => claim.criterionNumber === criterion.number,
            );
            return (
              <li key={criterion.id} id={`AC-${criterion.number}`} className={css.criterion}>
                <span className={css.id}>{id}</span>
                <Wording criterion={criterion} id={id} canWrite={canWrite} onChanged={onChanged} />
                <span className={css.proof}>
                  <ProofMark
                    state={proof?.state ?? 'unproven'}
                    reason={proof ? reasonOf(proof) : 'No test in the latest runs names it'}
                  />
                </span>
                <span className={css.tools}>
                  <Button variant="ghost" size="small" onPress={() => void copy(id)}>
                    {copied === id ? 'Copied' : 'Copy ID'}
                  </Button>
                  {canWrite ? (
                    <Button variant="ghost" size="small" onPress={() => setRemoving(criterion)}>
                      Remove
                    </Button>
                  ) : null}
                </span>
                {proof?.suspectSince && proof.tests > 0 ? (
                  <Suspect
                    id={id}
                    canWrite={canWrite}
                    isPending={confirm.isPending}
                    onConfirm={() => confirm.mutate(criterion)}
                  />
                ) : null}
                {claims.length ? <Tests claims={claims} proof={proof} /> : null}
              </li>
            );
          })}
        </ol>
      ) : (
        <p className={css.note}>This spec has no criteria yet, so nothing can prove it.</p>
      )}

      {canWrite ? (
        <form className={css.add} onSubmit={submit} noValidate>
          <TextField
            label="New criterion"
            value={text}
            onChange={setText}
            error={checked ? criterionProblem(text) : null}
            placeholder="When …, the system shall …"
          />
          <Button type="submit" variant="outline" isDisabled={add.isPending}>
            Add criterion
          </Button>
        </form>
      ) : null}
      <Notice
        text={add.error?.message ?? remove.error?.message ?? confirm.error?.message ?? null}
      />

      <Dialog
        title={`Remove ${removing ? criterionKey(spec.number, removing.number) : 'it'}?`}
        isOpen={removing !== null}
        onOpenChange={(open) => {
          if (!open) setRemoving(null);
        }}
        actions={
          <>
            <Button slot="close" variant="outline">
              Cancel
            </Button>
            <Button
              onPress={() => removing && remove.mutate(removing)}
              isDisabled={remove.isPending}
            >
              Remove
            </Button>
          </>
        }
      >
        <p>
          Tests that name it no longer prove anything here, and its ID won’t be given to another
          criterion. The spec’s history keeps a record of it.
        </p>
      </Dialog>
    </section>
  );
}

/** A criterion reworded while tests named it, whose tests a member confirms check the new wording. */
function Suspect({
  id,
  canWrite,
  isPending,
  onConfirm,
}: {
  id: string;
  canWrite: boolean;
  isPending: boolean;
  onConfirm: () => void;
}) {
  return (
    <span className={css.suspect}>
      <span>
        {id} was reworded after its tests ran, so they don’t prove it until someone confirms they
        check the new wording.
      </span>
      {canWrite ? (
        <Button variant="outline" size="small" onPress={onConfirm} isDisabled={isPending}>
          Its tests check this wording
        </Button>
      ) : null}
    </span>
  );
}

const outcomeNames: Record<Claim['outcome'], string> = {
  passed: 'Passed',
  failed: 'Failed',
  skipped: 'Skipped',
};

/** The tests in the latest runs that name a criterion, each with its outcome and its run. */
function Tests({ claims, proof }: { claims: readonly Claim[]; proof: CriterionProof | undefined }) {
  const count = claims.length === 1 ? '1 test' : `${claims.length} tests`;
  return (
    <details className={css.tests} open={proof?.state === 'failing'}>
      <summary>{count}</summary>
      <ul>
        {claims.map((claim) => (
          <li key={claim.id} className={css.test}>
            <span className={css.outcome} data-outcome={claim.outcome}>
              {outcomeNames[claim.outcome]}
            </span>
            <code>{claim.name}</code>
            <span className={css.where}>
              {claim.repository}, {claim.suite}, at{' '}
              <a href={commitUrl(claim.repository, claim.sha)}>{claim.sha.slice(0, 7)}</a>,{' '}
              <a href={runUrl(claim.repository, claim.runId)}>run {claim.runId}</a>
            </span>
            {claim.message ? <span className={css.message}>{claim.message}</span> : null}
          </li>
        ))}
      </ul>
    </details>
  );
}

/** A criterion's wording, which a member edits in place: Enter saves, Escape cancels. */
function Wording({
  criterion,
  id,
  canWrite,
  onChanged,
}: {
  criterion: Criterion;
  id: string;
  canWrite: boolean;
  onChanged: () => Promise<unknown>;
}) {
  const { client } = useAccount();
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(criterion.text);
  const reword = useMutation({
    mutationFn: () => rewordCriterion(client, criterion.id, text),
    onSuccess: async () => {
      setEditing(false);
      await onChanged();
    },
  });

  if (!editing) {
    return canWrite ? (
      <button
        type="button"
        className={css.text}
        onClick={() => {
          setText(criterion.text);
          setEditing(true);
        }}
        aria-label={`Edit ${id}: ${criterion.text}`}
      >
        {criterion.text}
      </button>
    ) : (
      <span className={css.text}>{criterion.text}</span>
    );
  }
  const onKeys = (event: KeyboardEvent) => {
    if (event.key === 'Escape') setEditing(false);
    if (event.key === 'Enter' && !criterionProblem(text)) {
      event.preventDefault();
      if (text.trim() === criterion.text) setEditing(false);
      else reword.mutate();
    }
  };
  return (
    <span className={css.text}>
      <TextField
        label={`${id}’s wording`}
        value={text}
        onChange={setText}
        onKeyDown={onKeys}
        onBlur={() => {
          if (!reword.isPending && text.trim() === criterion.text) setEditing(false);
        }}
        error={criterionProblem(text) ?? reword.error?.message ?? null}
        description="Enter saves; Escape cancels."
        autoFocus
      />
    </span>
  );
}

/** Who changed the spec and its criteria, and when, newest first. */
function History({
  spec,
  members,
  reviews,
}: {
  spec: Spec;
  members: readonly Member[];
  reviews: readonly Review[];
}) {
  const workspace = useWorkspace();
  const { data: changes, isPending, isError } = useHistory(workspace, spec.id);
  const { data: tasks } = useSpecTasks(workspace, spec.id);
  const context = {
    spec: spec.number,
    names: new Map(members.map((member) => [member.personId, member.name || member.email || ''])),
    criteria: new Map(spec.criteria.map((criterion) => [criterion.id, criterion.number])),
    reviewers: new Map(reviews.map((review) => [review.id, review.reviewerId])),
    tasks: new Map(tasks.map((task) => [task.id, task.number])),
  };

  return (
    <section className={css.section} aria-labelledby="history">
      <h2 id="history" className={css.heading}>
        History
      </h2>
      {isError ? (
        <p className={css.note}>The history didn’t load. Reload the page to try again.</p>
      ) : isPending ? null : (
        <ol className={css.history}>
          {changes.map((change) => (
            <li key={change.id}>
              <span>
                <strong>{whoOf(change)}</strong> {whatOf(change, context)}
              </span>
              <span className={css.when}>
                <When at={change.at} />
              </span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

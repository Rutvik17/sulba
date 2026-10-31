import { actorName } from '@sulba/data/requests';
import { criterionKey, specKey } from '@sulba/data/specs';
import {
  blockerProblem,
  moveTask,
  pullRequestName,
  pullRequestProblem,
  type Task,
  type TaskChange,
  type TaskStatus,
  taskKey,
  taskRoleMeanings,
  taskRoleNames,
  taskRoles,
  taskStatusNames,
  taskTitleProblem,
  updateTask,
} from '@sulba/data/tasks';
import { holds, type Member } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { Select } from '@sulba/ui/select';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import { type FormEvent, useState } from 'react';
import { useAccount } from './account';
import { type Command, useCommands } from './commands';
import { EditableTitle, SavedText } from './Editing';
import { Notice } from './Notice';
import { keys, useMembers, useTaskAt } from './queries';
import { useWorkspace } from './Shell';
import styles from './spec.module.css';
import ownStyles from './task.module.css';
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
  'facts',
  'unseen',
);
const own = classes(ownStyles, 'said', 'criteria', 'criterion', 'actions', 'form');

/** A way a person moves a task on, with the button that does it. */
interface Move {
  readonly to: TaskStatus;
  readonly label: string;
  /** Asks for a note, or a pull request and a note, before moving. */
  readonly asks?: 'blocker' | 'handIn';
}

/** The ways a member can move a task on from where it is. */
export function movesFrom(status: TaskStatus): Move[] {
  const done: Move = { to: 'done', label: 'Mark done' };
  const cancel: Move = { to: 'canceled', label: 'Cancel task' };
  const release: Move = { to: 'open', label: 'Release' };
  switch (status) {
    case 'open':
      return [{ to: 'in_progress', label: 'Take it' }, cancel];
    case 'in_progress':
      return [
        { to: 'in_review', label: 'Hand in', asks: 'handIn' },
        { to: 'blocked', label: 'Block', asks: 'blocker' },
        done,
        release,
        cancel,
      ];
    case 'blocked':
      return [{ to: 'in_progress', label: 'Resume' }, done, release, cancel];
    case 'in_review':
      return [done, { to: 'in_progress', label: 'Send back' }, release, cancel];
    default:
      return [{ to: 'open', label: 'Open again' }];
  }
}

/**
 * A task's page, at its ID: TASK-7 (decision record 61). What to do, the spec's criteria it
 * covers, who has it and its pull request, and the buttons that move it on.
 */
export function TaskPage({ number }: { number: number }) {
  const workspace = useWorkspace();
  const { data: task } = useTaskAt(workspace, number);
  const { data: members } = useMembers(workspace);
  if (!task) return <NoTask number={number} />;
  return <Page task={task} members={members} />;
}

function NoTask({ number }: { number: number }) {
  const workspace = useWorkspace();
  useTitle('No task here', workspace.name);
  return (
    <div className={css.main}>
      <h1 className={css.title}>No task here</h1>
      <p className={css.note}>{`${taskKey(number)} hasn’t been written in this workspace.`}</p>
      <Link to="/$slug/tasks" params={{ slug: workspace.slug }}>
        Go to the tasks
      </Link>
    </div>
  );
}

function Page({ task, members }: { task: Task; members: readonly Member[] }) {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const canWrite = holds(workspace.role, 'member');
  const key = taskKey(task.number);
  useTitle(`${key} ${task.title}`, workspace.name);
  const [failure, setFailure] = useState<string | null>(null);
  const [asking, setAsking] = useState<Move | null>(null);
  const names = new Map(members.map((member) => [member.personId, member.name || member.email]));

  const reread = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: keys.task(workspace.id, task.number) }),
      queryClient.invalidateQueries({ queryKey: keys.tasks(workspace.id) }),
      queryClient.invalidateQueries({ queryKey: keys.work(workspace.id) }),
      queryClient.invalidateQueries({ queryKey: keys.history(task.spec.id) }),
    ]);
  const change = useMutation({
    mutationFn: (patch: TaskChange) => updateTask(client, task.id, patch),
    onMutate: () => setFailure(null),
    onSuccess: reread,
    onError: (error) => setFailure(error.message),
  });
  const move = useMutation({
    mutationFn: ({ to, ...said }: { to: TaskStatus; note?: string; pullRequest?: string }) =>
      moveTask(client, task.id, to, said),
    onMutate: () => setFailure(null),
    onSuccess: async () => {
      setAsking(null);
      await reread();
    },
    onError: (error) => setFailure(error.message),
  });
  const moves = canWrite ? movesFrom(task.status) : [];
  const start = (each: Move) => (each.asks ? setAsking(each) : move.mutate({ to: each.to }));

  useCommands(
    moves.length
      ? [
          {
            id: 'task-status',
            label: 'Move task',
            group: key,
            keys: ['s'],
            does: {
              title: 'Move task',
              actions: moves.map((each) => ({
                id: `${each.to}-${each.label}`,
                label: each.asks ? `${each.label}…` : each.label,
                run: () => start(each),
              })),
            },
          } satisfies Command,
        ]
      : [],
  );

  const taker =
    task.takenBy === null && task.takenByAgent === null
      ? null
      : actorName(task.takenBy && names.get(task.takenBy), task.takenByAgent);

  return (
    <div className={css.spec}>
      <div className={css.head}>
        <nav aria-label="Breadcrumb" className={css.crumbs}>
          <Link to="/$slug/tasks" params={{ slug: workspace.slug }}>
            Tasks
          </Link>
          <span aria-hidden="true">/</span>
          <span className={css.key}>{key}</span>
        </nav>
        <EditableTitle
          title={task.title}
          canWrite={canWrite}
          problemOf={taskTitleProblem}
          onSave={(title) => change.mutate({ title })}
        />
        <Notice text={failure} />
      </div>

      <div className={css.main}>
        {task.note && (task.status === 'blocked' || task.status === 'in_review') ? (
          <section
            className={own.said}
            aria-label={task.status === 'blocked' ? 'What blocks it' : 'Handed in'}
          >
            <p>
              <strong>{task.status === 'blocked' ? 'Blocked' : 'Handed in'}</strong>
              {taker ? ` by ${taker}` : null}
            </p>
            <p>{task.note}</p>
          </section>
        ) : null}

        <section className={css.section} aria-labelledby="instructions">
          <h2 id="instructions" className={css.unseen}>
            Instructions
          </h2>
          <SavedText
            text={task.body}
            label={`${key}’s instructions`}
            placeholder="What to do, where, and what done means. Markdown works here."
            canWrite={canWrite}
            save={async (body) => {
              await updateTask(client, task.id, { body });
            }}
          />
        </section>

        <section className={css.section} aria-labelledby="covers">
          <h2 id="covers" className={css.heading}>
            Criteria it covers
          </h2>
          {task.criteria.length === 0 ? (
            <p className={css.note}>It names none of {specKey(task.spec.number)}’s criteria.</p>
          ) : (
            <ul className={own.criteria}>
              {task.criteria.map((criterion) => (
                <li key={criterion.number} className={own.criterion}>
                  <span className={css.key}>
                    {criterionKey(task.spec.number, criterion.number)}
                  </span>
                  <span>{criterion.text}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <aside className={css.side} aria-label="Details">
        <dl className={css.facts}>
          <div>
            <dt>Status</dt>
            <dd>{taskStatusNames[task.status]}</dd>
          </div>
          <div>
            <dt>Role</dt>
            <dd>
              {canWrite ? (
                <Select
                  label="Role"
                  hideLabel
                  size="small"
                  options={taskRoles.map((id) => ({
                    id,
                    name: taskRoleNames[id],
                    description: taskRoleMeanings[id],
                  }))}
                  value={task.role}
                  onChange={(role) => change.mutate({ role })}
                  isDisabled={change.isPending}
                />
              ) : (
                taskRoleNames[task.role]
              )}
            </dd>
          </div>
          <div>
            <dt>Spec</dt>
            <dd>
              <Link
                to="/$slug/$spec"
                params={{ slug: workspace.slug, spec: specKey(task.spec.number) }}
              >
                {specKey(task.spec.number)} {task.spec.title}
              </Link>
            </dd>
          </div>
          <div>
            <dt>Taken by</dt>
            <dd>{taker ?? 'No one'}</dd>
          </div>
          <div>
            <dt>Pull request</dt>
            <dd>
              {task.pullRequest ? (
                <a href={task.pullRequest} target="_blank" rel="noreferrer">
                  {pullRequestName(task.pullRequest)}
                </a>
              ) : (
                'None yet'
              )}
            </dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>
              <When at={task.createdAt} day />
            </dd>
          </div>
          <div>
            <dt>Updated</dt>
            <dd>
              <When at={task.updatedAt} />
            </dd>
          </div>
        </dl>
        {moves.length ? (
          <div className={own.actions}>
            {moves.map((each, index) => (
              <Button
                key={`${each.to}-${each.label}`}
                size="small"
                variant={index === 0 ? 'primary' : 'outline'}
                onPress={() => start(each)}
                isDisabled={move.isPending}
              >
                {each.asks ? `${each.label}…` : each.label}
              </Button>
            ))}
          </div>
        ) : null}
      </aside>

      <Said
        key={asking?.label ?? 'none'}
        move={asking}
        task={task}
        onClose={() => setAsking(null)}
        onSend={(said) => asking && move.mutate({ to: asking.to, ...said })}
        failure={move.error?.message ?? null}
        isPending={move.isPending}
      />
    </div>
  );
}

/**
 * Asks what blocks a task, or the pull request that holds its work, before moving it. Each move
 * opens it afresh, so what was typed for one isn't sent with another.
 */
function Said({
  move,
  task,
  onClose,
  onSend,
  failure,
  isPending,
}: {
  move: Move | null;
  task: Task;
  onClose: () => void;
  onSend: (said: { note?: string; pullRequest?: string }) => void;
  failure: string | null;
  isPending: boolean;
}) {
  const [note, setNote] = useState('');
  const [address, setAddress] = useState(task.pullRequest ?? '');
  const [checked, setChecked] = useState(false);
  const handIn = move?.asks === 'handIn';
  const noteError = checked && !handIn ? blockerProblem(note) : null;
  const addressError = checked && handIn ? pullRequestProblem(address) : null;
  const close = () => {
    setNote('');
    setChecked(false);
    onClose();
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setChecked(true);
    if (handIn ? pullRequestProblem(address) : blockerProblem(note)) return;
    onSend(handIn ? { pullRequest: address, ...(note.trim() ? { note } : {}) } : { note });
  };
  const key = taskKey(task.number);

  return (
    <Dialog
      title={handIn ? `Hand in ${key}` : `Block ${key}`}
      isOpen={move !== null}
      onOpenChange={(open) => {
        if (!open) close();
      }}
      actions={
        <>
          <Button slot="close" variant="outline">
            Cancel
          </Button>
          <Button type="submit" form="task-said" isDisabled={isPending}>
            {handIn ? 'Hand in' : 'Block'}
          </Button>
        </>
      }
    >
      <form id="task-said" className={own.form} onSubmit={submit} noValidate>
        {handIn ? (
          <TextField
            label="Pull request"
            value={address}
            onChange={setAddress}
            error={addressError}
            placeholder="https://github.com/acme-co/booking/pull/12"
            description="In one of the workspace’s repositories."
            autoFocus
          />
        ) : null}
        <TextField
          label={handIn ? 'What it does' : 'What blocks it?'}
          value={note}
          onChange={setNote}
          multiline
          error={noteError}
          {...(handIn ? {} : { autoFocus: true })}
        />
        <Notice text={failure} />
      </form>
    </Dialog>
  );
}

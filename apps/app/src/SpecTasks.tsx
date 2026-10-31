import { actorName } from '@sulba/data/requests';
import { type Spec, specKey } from '@sulba/data/specs';
import {
  createTask,
  type TaskRole,
  taskKey,
  taskRoleMeanings,
  taskRoleNames,
  taskRoles,
  taskStatusNames,
  taskTitleProblem,
} from '@sulba/data/tasks';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { Select } from '@sulba/ui/select';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from '@tanstack/react-router';
import { type FormEvent, useState } from 'react';
import { useAccount } from './account';
import { Notice } from './Notice';
import pageStyles from './page.module.css';
import { keys, useMembers, useSpecTasks } from './queries';
import ownStyles from './request.module.css';
import { useWorkspace } from './Shell';
import styles from './spec.module.css';

const css = classes(styles, 'section', 'heading', 'note', 'key');
const own = classes(ownStyles, 'drafted', 'spec', 'status');
const page = classes(pageStyles, 'form');

/**
 * The tasks an approved spec is split into, each with its status and who has it (decision record
 * 61), and, for a member, the button that writes one.
 */
export function SpecTasks({ spec, canWrite }: { spec: Spec; canWrite: boolean }) {
  const workspace = useWorkspace();
  const { data: tasks } = useSpecTasks(workspace, spec.id);
  const { data: members } = useMembers(workspace);
  const [writing, setWriting] = useState(false);
  const names = new Map(members.map((member) => [member.personId, member.name || member.email]));
  const approved = spec.status === 'approved' || spec.status === 'implemented';
  if (!approved && tasks.length === 0) return null;

  return (
    <section className={css.section} aria-labelledby="tasks">
      <h2 id="tasks" className={css.heading}>
        Tasks
      </h2>
      {tasks.length === 0 ? (
        <p className={css.note}>
          No tasks yet. A connected agent can split the spec into tasks, or you can write one.
        </p>
      ) : (
        <ul className={own.drafted}>
          {tasks.map((task) => (
            <li key={task.id} className={own.spec}>
              <span className={css.key}>{taskKey(task.number)}</span>
              <Link to="/$slug/$spec" params={{ slug: workspace.slug, spec: taskKey(task.number) }}>
                {task.title}
              </Link>
              <span className={own.status}>
                {taskRoleNames[task.role]} · {taskStatusNames[task.status]}
                {task.status !== 'open' && (task.takenBy || task.takenByAgent)
                  ? ` · ${actorName(task.takenBy && names.get(task.takenBy), task.takenByAgent)}`
                  : null}
              </span>
            </li>
          ))}
        </ul>
      )}
      {canWrite && approved ? (
        <div>
          <Button variant="outline" size="small" onPress={() => setWriting(true)}>
            Write a task
          </Button>
        </div>
      ) : null}
      <NewTask spec={spec} isOpen={writing} onClose={() => setWriting(false)} />
    </section>
  );
}

/** Writes a task from the spec, covering all its criteria, then opens it. */
function NewTask({ spec, isOpen, onClose }: { spec: Spec; isOpen: boolean; onClose: () => void }) {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [role, setRole] = useState<TaskRole>('build');
  const [body, setBody] = useState('');
  const [checked, setChecked] = useState(false);

  const close = () => {
    onClose();
    setTitle('');
    setRole('build');
    setBody('');
    setChecked(false);
    create.reset();
  };
  const create = useMutation({
    mutationFn: () =>
      createTask(client, spec.id, {
        title,
        role,
        body,
        criteria: spec.criteria.map((criterion) => criterion.number),
      }),
    onSuccess: async (number) => {
      await queryClient.invalidateQueries({ queryKey: keys.tasks(workspace.id) });
      close();
      await navigate({
        to: '/$slug/$spec',
        params: { slug: workspace.slug, spec: taskKey(number) },
      });
    },
  });
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setChecked(true);
    if (taskTitleProblem(title)) return;
    create.mutate();
  };
  const covered =
    spec.criteria.length === 0
      ? `${specKey(spec.number)} has no criteria yet.`
      : `It covers ${spec.criteria.length === 1 ? 'the' : `all ${spec.criteria.length} of`} ${specKey(spec.number)}’s ${spec.criteria.length === 1 ? 'criterion' : 'criteria'}.`;

  return (
    <Dialog
      title={`New task for ${specKey(spec.number)}`}
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) close();
      }}
      actions={
        <>
          <Button slot="close" variant="outline">
            Cancel
          </Button>
          <Button type="submit" form="new-task" isDisabled={create.isPending}>
            {create.isPending ? 'Writing…' : 'Write task'}
          </Button>
        </>
      }
    >
      <form id="new-task" className={page.form} onSubmit={submit} noValidate>
        <TextField
          label="Title"
          value={title}
          onChange={setTitle}
          error={checked ? taskTitleProblem(title) : null}
          placeholder="Build the booking endpoint"
          autoFocus
        />
        <Select
          label="Role"
          options={taskRoles.map((id) => ({
            id,
            name: taskRoleNames[id],
            description: taskRoleMeanings[id],
          }))}
          value={role}
          onChange={setRole}
        />
        <TextField
          label="Instructions"
          value={body}
          onChange={setBody}
          multiline
          description={covered}
          placeholder="What to do, where, and what done means."
        />
        <Notice text={create.error?.message ?? null} />
      </form>
    </Dialog>
  );
}

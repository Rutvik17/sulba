import { actorName } from '@sulba/data/requests';
import { specKey } from '@sulba/data/specs';
import { taskKey, taskRoleNames, taskStatusNames } from '@sulba/data/tasks';
import { classes } from '@sulba/ui/classes';
import { Link } from '@tanstack/react-router';
import styles from './page.module.css';
import { useMembers, useTasks } from './queries';
import { useWorkspace } from './Shell';
import { useTitle } from './title';
import { When } from './When';

const css = classes(
  styles,
  'page',
  'header',
  'title',
  'count',
  'note',
  'scroll',
  'table',
  'key',
  'name',
  'dim',
  'numeric',
  'empty',
);

/**
 * Every task in the workspace, newest first: the work its approved specs are split into, with who
 * has each one (decision record 61). Tasks are written from a spec's page, or by agents.
 */
export function Tasks() {
  const workspace = useWorkspace();
  useTitle('Tasks', workspace.name);
  const { data: tasks } = useTasks(workspace);
  const { data: members } = useMembers(workspace);
  const names = new Map(members.map((member) => [member.personId, member.name || member.email]));
  const count = tasks.length === 1 ? '1 task' : `${tasks.length} tasks`;

  return (
    <div className={css.page}>
      <header className={css.header}>
        <div>
          <h1 className={css.title}>Tasks</h1>
          {tasks.length ? <p className={css.count}>{count}</p> : null}
        </div>
      </header>

      {tasks.length === 0 ? (
        <section className={css.empty} aria-label="No tasks yet">
          <p>
            A task is one piece of work from an approved spec, for one pull request. Write one from
            the spec’s page, or let a connected agent split the spec into tasks and take them.
          </p>
          <Link to="/$slug/specs" params={{ slug: workspace.slug }}>
            Go to the specs
          </Link>
        </section>
      ) : (
        <div className={css.scroll}>
          <table className={css.table}>
            <thead>
              <tr>
                <th scope="col">ID</th>
                <th scope="col">Title</th>
                <th scope="col">Role</th>
                <th scope="col">Spec</th>
                <th scope="col">Status</th>
                <th scope="col">Taken by</th>
                <th scope="col">Updated</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => {
                const key = taskKey(task.number);
                return (
                  <tr key={task.id}>
                    <td className={css.key}>{key}</td>
                    <td>
                      <Link
                        to="/$slug/$spec"
                        params={{ slug: workspace.slug, spec: key }}
                        className={css.name}
                      >
                        {task.title}
                      </Link>
                    </td>
                    <td>{taskRoleNames[task.role]}</td>
                    <td className={css.key}>{specKey(task.spec.number)}</td>
                    <td>{taskStatusNames[task.status]}</td>
                    <td>
                      {task.status === 'open' ||
                      (task.takenBy === null && task.takenByAgent === null) ? (
                        <span className={css.dim}>No one</span>
                      ) : (
                        actorName(task.takenBy && names.get(task.takenBy), task.takenByAgent)
                      )}
                    </td>
                    <td className={css.numeric}>
                      <When at={task.updatedAt} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

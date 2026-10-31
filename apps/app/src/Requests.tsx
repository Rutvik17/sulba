import { requestKey, requestStatusNames } from '@sulba/data/requests';
import { holds } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Link } from '@tanstack/react-router';
import { useCreateRequest } from './commands';
import styles from './page.module.css';
import { useMembers, useRequests } from './queries';
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
 * Every request in the workspace, newest first: what someone wants built, in their own words, with
 * the questions waiting on its writer and the specs drafted from it (decision record 60).
 */
export function Requests() {
  const workspace = useWorkspace();
  useTitle('Requests', workspace.name);
  const { data: requests } = useRequests(workspace);
  const { data: members } = useMembers(workspace);
  const createRequest = useCreateRequest();
  const canWrite = holds(workspace.role, 'member');
  const names = new Map(members.map((member) => [member.personId, member.name || member.email]));
  const count = requests.length === 1 ? '1 request' : `${requests.length} requests`;

  return (
    <div className={css.page}>
      <header className={css.header}>
        <div>
          <h1 className={css.title}>Requests</h1>
          {requests.length ? <p className={css.count}>{count}</p> : null}
        </div>
        {canWrite ? <Button onPress={createRequest}>New request</Button> : null}
      </header>

      {requests.length === 0 ? (
        <section className={css.empty} aria-label="No requests yet">
          <p>
            A request says what you want built, in your own words. A connected agent asks you what
            it needs to know, then drafts the specs for your team to approve.
          </p>
          {canWrite ? (
            <Button onPress={createRequest}>Write the first request</Button>
          ) : (
            <p className={css.note}>No one has written a request here yet.</p>
          )}
        </section>
      ) : (
        <div className={css.scroll}>
          <table className={css.table}>
            <thead>
              <tr>
                <th scope="col">ID</th>
                <th scope="col">Title</th>
                <th scope="col">Status</th>
                <th scope="col">Questions</th>
                <th scope="col">Specs</th>
                <th scope="col">Writer</th>
                <th scope="col">Updated</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((request) => {
                const key = requestKey(request.number);
                return (
                  <tr key={request.id}>
                    <td className={css.key}>{key}</td>
                    <td>
                      <Link
                        to="/$slug/$spec"
                        params={{ slug: workspace.slug, spec: key }}
                        className={css.name}
                      >
                        {request.title}
                      </Link>
                    </td>
                    <td>{requestStatusNames[request.status]}</td>
                    <td className={css.numeric}>
                      {request.unanswered ? (
                        `${request.unanswered} to answer`
                      ) : (
                        <span className={css.dim}>None open</span>
                      )}
                    </td>
                    <td className={css.numeric}>{request.specs}</td>
                    <td>
                      {(request.createdBy && names.get(request.createdBy)) || (
                        <span className={css.dim}>Someone who has left</span>
                      )}
                    </td>
                    <td className={css.numeric}>
                      <When at={request.updatedAt} />
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

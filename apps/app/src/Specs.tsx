import { criterionKey, specKey, statusNames } from '@sulba/data/specs';
import { holds } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Tooltip } from '@sulba/ui/tooltip';
import { Link } from '@tanstack/react-router';
import { shortcutSteps, useCreateSpec } from './commands';
import { ago, momentOf } from './format';
import styles from './page.module.css';
import { specProofText } from './proofs';
import { useMembers, useSpecProofs, useSpecs } from './queries';
import { useWorkspace } from './Shell';
import { useTitle } from './title';

const css = classes(
  styles,
  'page',
  'header',
  'title',
  'count',
  'section',
  'note',
  'scroll',
  'table',
  'key',
  'name',
  'dim',
  'numeric',
  'empty',
);

/** Every spec in the workspace, newest first, with its status, criteria and owner. */
export function Specs() {
  const workspace = useWorkspace();
  useTitle('Specs', workspace.name);
  const { data: specs } = useSpecs(workspace);
  const { data: members } = useMembers(workspace);
  const { data: proofs } = useSpecProofs(workspace);
  const createSpec = useCreateSpec();
  const canWrite = holds(workspace.role, 'member');
  const names = new Map(members.map((member) => [member.personId, member.name || member.email]));
  const count = specs.length === 1 ? '1 spec' : `${specs.length} specs`;

  return (
    <div className={css.page}>
      <header className={css.header}>
        <div>
          <h1 className={css.title}>Specs</h1>
          {specs.length ? <p className={css.count}>{count}</p> : null}
        </div>
        {canWrite ? (
          <Tooltip keys={shortcutSteps(['c'])}>
            <Button onPress={createSpec} aria-keyshortcuts="C">
              New spec
            </Button>
          </Tooltip>
        ) : null}
      </header>

      {specs.length === 0 ? (
        <section className={css.empty} aria-label="No specs yet">
          <p>
            A spec says what to build, and its acceptance criteria say when it’s done. A test proves
            a criterion by naming its ID, such as <code>{criterionKey(1, 1)}</code>, in its name.
          </p>
          {canWrite ? (
            <Button onPress={createSpec}>Write the first spec</Button>
          ) : (
            <p className={css.note}>No one has written a spec here yet.</p>
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
                <th scope="col">Criteria</th>
                <th scope="col">Proof</th>
                <th scope="col">Owner</th>
                <th scope="col">Updated</th>
              </tr>
            </thead>
            <tbody>
              {specs.map((spec) => {
                const key = specKey(spec.number);
                return (
                  <tr key={spec.id}>
                    <td className={css.key}>{key}</td>
                    <td>
                      <Link
                        to="/$slug/$spec"
                        params={{ slug: workspace.slug, spec: key }}
                        className={css.name}
                      >
                        {spec.title}
                      </Link>
                    </td>
                    <td>{statusNames[spec.status]}</td>
                    <td className={css.numeric}>{spec.criteria}</td>
                    <td className={css.numeric}>
                      {proofs ? specProofText(proofs.get(spec.id)) : null}
                    </td>
                    <td>
                      {spec.ownerId ? (
                        (names.get(spec.ownerId) ?? '')
                      ) : (
                        <span className={css.dim}>No owner</span>
                      )}
                    </td>
                    <td className={css.numeric} title={momentOf(spec.updatedAt)}>
                      {ago(spec.updatedAt)}
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

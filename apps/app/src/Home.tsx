import { roleNames } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Link, Navigate } from '@tanstack/react-router';
import { useAccount, useSignOut } from './account';
import { Centered } from './Centered';
import styles from './Home.module.css';
import { lastWorkspace } from './last';
import { NewWorkspace } from './NewWorkspace';
import { useWorkspaces } from './queries';

const css = classes(styles, 'list', 'row', 'name', 'meta', 'foot', 'who');

/**
 * The app's front door for someone signed in: back to the workspace they opened last, straight
 * into their only one, a list to pick from, or, with none yet, a form to create one.
 */
export function Home() {
  const { data: workspaces } = useWorkspaces();
  const { email } = useAccount();
  const signOut = useSignOut();

  const last = lastWorkspace();
  const next =
    workspaces.find(({ slug }) => slug === last) ??
    (workspaces.length === 1 ? workspaces[0] : undefined);
  if (next) return <Navigate to="/$slug" params={{ slug: next.slug }} replace />;
  if (workspaces.length === 0) return <NewWorkspace />;

  return (
    <Centered title="Your workspaces">
      <ul className={css.list}>
        {workspaces.map(({ slug, name, role }) => (
          <li key={slug}>
            <Link to="/$slug" params={{ slug }} className={css.row}>
              <span className={css.name}>{name}</span>
              <span className={css.meta}>
                sulba.dev/app/{slug} · {roleNames[role]}
              </span>
            </Link>
          </li>
        ))}
      </ul>
      <div className={css.foot}>
        <Link to="/new">Create a workspace</Link>
        <span className={css.who}>
          {email ? `Signed in as ${email}` : null}
          <Button variant="ghost" size="small" onPress={() => void signOut()}>
            Sign out
          </Button>
        </span>
      </div>
    </Centered>
  );
}

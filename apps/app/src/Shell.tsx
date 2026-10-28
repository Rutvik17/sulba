import type { Workspace } from '@sulba/data/workspaces';
import { classes } from '@sulba/ui/classes';
import { Menu, MenuItem, MenuTrigger } from '@sulba/ui/menu';
import { Link, Outlet, useMatchRoute, useNavigate, useParams } from '@tanstack/react-router';
import { createContext, use, useEffect } from 'react';
import { Button } from 'react-aria-components/Button';
import { useSignOut } from './account';
import { Centered } from './Centered';
import { rememberWorkspace } from './last';
import { Mark } from './Mark';
import { useWorkspaceAt, useWorkspaces } from './queries';
import styles from './Shell.module.css';

const css = classes(
  styles,
  'shell',
  'sidebar',
  'switcher',
  'current',
  'chevron',
  'nav',
  'link',
  'main',
);

const WorkspaceContext = createContext<Workspace | null>(null);

/** The workspace a page inside the shell belongs to. */
export function useWorkspace(): Workspace {
  const workspace = use(WorkspaceContext);
  if (!workspace) throw new Error('useWorkspace is for pages inside a workspace');
  return workspace;
}

/**
 * Every page of a workspace: the sidebar, with the workspace's name, which switches workspaces,
 * and its pages, and the page beside it. On a phone the sidebar becomes a bar across the top.
 */
export function Shell() {
  const { slug } = useParams({ from: '/$slug' });
  const { data: workspace } = useWorkspaceAt(slug);
  // A spec's page sits under Specs in the sidebar, though its address is the spec's ID.
  const onSpec = Boolean(useMatchRoute()({ to: '/$slug/$spec', params: { slug } }));

  useEffect(() => {
    if (workspace) rememberWorkspace(workspace.slug);
  }, [workspace]);

  if (!workspace) {
    return (
      <Centered
        title="No workspace here"
        lead={`There’s no workspace at sulba.dev/app/${slug}, or you aren’t one of its members.`}
      >
        <Link to="/">Go to your workspaces</Link>
      </Centered>
    );
  }

  return (
    <WorkspaceContext value={workspace}>
      <div className={css.shell}>
        <aside className={css.sidebar}>
          <Switcher current={workspace} />
          <nav aria-label="Workspace" className={css.nav}>
            <Link
              to="/$slug"
              params={{ slug }}
              activeOptions={{ exact: true }}
              className={css.link}
            >
              My work
            </Link>
            <Link
              to="/$slug/specs"
              params={{ slug }}
              className={css.link}
              {...(onSpec ? { 'aria-current': 'page' as const } : {})}
            >
              Specs
            </Link>
            <Link to="/$slug/evidence" params={{ slug }} className={css.link}>
              Evidence
            </Link>
            <Link to="/$slug/members" params={{ slug }} className={css.link}>
              Members
            </Link>
            <Link to="/$slug/settings" params={{ slug }} className={css.link}>
              Settings
            </Link>
          </nav>
        </aside>
        <main className={css.main}>
          <Outlet />
        </main>
      </div>
    </WorkspaceContext>
  );
}

function Switcher({ current }: { current: Workspace }) {
  const { data: workspaces } = useWorkspaces();
  const navigate = useNavigate();
  const signOut = useSignOut();

  const choose = async (key: string) => {
    if (key === 'new') return navigate({ to: '/new' });
    if (key === 'sign-out') {
      await signOut();
      return navigate({ to: '/' });
    }
    return navigate({ to: '/$slug', params: { slug: key } });
  };

  return (
    <MenuTrigger>
      <Button className={css.switcher} aria-label={`${current.name}, switch workspace`}>
        <Mark />
        <span className={css.current}>{current.name}</span>
        <svg className={css.chevron} viewBox="0 0 12 12" aria-hidden="true">
          <path d="M3 4.5 6 7.5 9 4.5" />
        </svg>
      </Button>
      <Menu onAction={(key) => void choose(String(key))}>
        {workspaces.map(({ slug, name }) => (
          <MenuItem key={slug} id={slug}>
            {slug === current.slug ? `${name} (this workspace)` : name}
          </MenuItem>
        ))}
        <MenuItem id="new">Create a workspace</MenuItem>
        <MenuItem id="sign-out">Sign out</MenuItem>
      </Menu>
    </MenuTrigger>
  );
}

import { requestNumberOf } from '@sulba/data/requests';
import { taskNumberOf } from '@sulba/data/tasks';
import type { Workspace } from '@sulba/data/workspaces';
import { classes } from '@sulba/ui/classes';
import { Keys } from '@sulba/ui/keys';
import { Menu, MenuItem, MenuTrigger } from '@sulba/ui/menu';
import { Link, Outlet, useMatches, useNavigate, useParams } from '@tanstack/react-router';
import { createContext, use, useEffect } from 'react';
import { Button } from 'react-aria-components/Button';
import { useSignOut } from './account';
import { Centered } from './Centered';
import { Commands, menuShortcut, shortcutSteps, useOpenMenu } from './commands';
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
  'search',
  'nav',
  'link',
  'keys',
  'main',
);

/** The sidebar's pages, with the keys that go to each. */
const pages = [
  { to: '/$slug', label: 'My work', keys: ['g', 'w'] },
  { to: '/$slug/requests', label: 'Requests', keys: ['g', 'r'] },
  { to: '/$slug/specs', label: 'Specs', keys: ['g', 's'] },
  { to: '/$slug/tasks', label: 'Tasks', keys: ['g', 't'] },
  { to: '/$slug/evidence', label: 'Evidence', keys: ['g', 'e'] },
  { to: '/$slug/members', label: 'Members', keys: ['g', 'm'] },
  { to: '/$slug/settings', label: 'Settings', keys: ['g', ','] },
] as const;

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
  // A spec's page sits under Specs in the sidebar, a request's under Requests and a task's under
  // Tasks, though each one's address is its ID. Matching the route itself, not its pattern, keeps /$slug/members and
  // the others from looking like one.
  const item = useMatches({
    select: (matches) => {
      const match = matches.find((each) => each.routeId === '/$slug/$spec');
      return match && 'spec' in match.params ? match.params.spec : null;
    },
  });
  const itemSection =
    item === null
      ? null
      : requestNumberOf(item) !== null
        ? '/$slug/requests'
        : taskNumberOf(item) !== null
          ? '/$slug/tasks'
          : '/$slug/specs';

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
      <Commands>
        <div className={css.shell}>
          <aside className={css.sidebar}>
            <Switcher current={workspace} />
            <Search />
            <nav aria-label="Workspace" className={css.nav}>
              {pages.map((page) => (
                <Link
                  key={page.to}
                  to={page.to}
                  params={{ slug }}
                  activeOptions={{ exact: page.to === '/$slug' }}
                  className={css.link}
                  {...(page.to === itemSection ? { 'aria-current': 'page' as const } : {})}
                >
                  {page.label}
                  <span className={css.keys} aria-hidden="true">
                    <Keys steps={shortcutSteps(page.keys)} />
                  </span>
                </Link>
              ))}
            </nav>
          </aside>
          <main className={css.main}>
            <Outlet />
          </main>
        </div>
      </Commands>
    </WorkspaceContext>
  );
}

/** The button that opens the command menu, which also finds specs. */
function Search() {
  const open = useOpenMenu();
  return (
    <Button className={css.search} onPress={open} aria-keyshortcuts={menuShortcut}>
      <span>Search…</span>
      <span aria-hidden="true">
        <Keys steps={shortcutSteps(['mod+k'])} />
      </span>
    </Button>
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

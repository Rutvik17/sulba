import {
  createRootRoute,
  createRoute,
  createRouter,
  type ErrorComponentProps,
  lazyRouteComponent,
  Outlet,
  redirect,
} from '@tanstack/react-router';
import { type ReactNode, Suspense } from 'react';
import { RequireAccount } from './account';
import { Evidence } from './Evidence';
import { Failed, NotFound } from './fallbacks';
import { Home } from './Home';
import { Join } from './Join';
import { Members } from './Members';
import { NewWorkspace } from './NewWorkspace';
import { Settings } from './Settings';
import { Shell } from './Shell';
import { SignIn } from './SignIn';
import { Specs } from './Specs';

/** A page for someone signed in. A page waits for what it reads without showing a spinner. */
const signedIn = (page: () => ReactNode) => () => (
  <RequireAccount signIn={<SignIn />}>
    <Suspense fallback={null}>{page()}</Suspense>
  </RequireAccount>
);

const root = createRootRoute({
  component: Outlet,
  notFoundComponent: NotFound,
  errorComponent: ({ error, reset }: ErrorComponentProps) => <Failed error={error} retry={reset} />,
});

const home = createRoute({
  getParentRoute: () => root,
  path: '/',
  component: signedIn(() => <Home />),
});
const create = createRoute({
  getParentRoute: () => root,
  path: '/new',
  component: signedIn(() => <NewWorkspace />),
});
const join = createRoute({ getParentRoute: () => root, path: '/join/$token', component: Join });

const workspace = createRoute({
  getParentRoute: () => root,
  path: '/$slug',
  component: signedIn(() => <Shell />),
});
const opened = createRoute({
  getParentRoute: () => workspace,
  path: '/',
  beforeLoad: ({ params }) => {
    throw redirect({ to: '/$slug/specs', params, replace: true });
  },
});
const specs = createRoute({ getParentRoute: () => workspace, path: '/specs', component: Specs });
// A spec's page brings the Markdown editor, which loads only once a spec is opened.
const spec = createRoute({
  getParentRoute: () => workspace,
  path: '/$spec',
  component: lazyRouteComponent(() => import('./SpecPage'), 'SpecPage'),
});
const evidence = createRoute({
  getParentRoute: () => workspace,
  path: '/evidence',
  component: Evidence,
});
const members = createRoute({
  getParentRoute: () => workspace,
  path: '/members',
  component: Members,
});
const settings = createRoute({
  getParentRoute: () => workspace,
  path: '/settings',
  component: Settings,
});

/** The app's pages, under /app/ on the site. */
export const router = createRouter({
  routeTree: root.addChildren([
    home,
    create,
    join,
    workspace.addChildren([opened, specs, evidence, members, settings, spec]),
  ]),
  basepath: '/app',
  defaultPreload: 'intent',
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

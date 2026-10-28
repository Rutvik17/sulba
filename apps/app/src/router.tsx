import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router';
import { Home } from './Home';
import { Layout } from './Layout';
import { NotFound } from './NotFound';

const root = createRootRoute({ component: Layout, notFoundComponent: NotFound });
const home = createRoute({ getParentRoute: () => root, path: '/', component: Home });

/** The app's pages, under /app/ on the site. */
export const router = createRouter({ routeTree: root.addChildren([home]), basepath: '/app' });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

import '@fontsource-variable/geist';
import '@fontsource-variable/geist-mono';
import '@sulba/ui/tokens.css';
import '@sulba/ui/base.css';
import './app.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from '@tanstack/react-router';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { AccountProvider } from './account';
import { router } from './router';

const element = document.getElementById('app');
if (!element) throw new Error('index.html has no #app element');

// What a page reads stays fresh for 30 seconds, so moving between pages doesn't ask again.
const queries = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

createRoot(element).render(
  <StrictMode>
    <QueryClientProvider client={queries}>
      <AccountProvider>
        <RouterProvider router={router} />
      </AccountProvider>
    </QueryClientProvider>
  </StrictMode>,
);

import '@fontsource-variable/geist';
import '@fontsource-variable/geist-mono';
import '@sulba/ui/tokens.css';
import '@sulba/ui/base.css';
import './app.css';
import { RouterProvider } from '@tanstack/react-router';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { router } from './router';

const element = document.getElementById('app');
if (!element) throw new Error('index.html has no #app element');

createRoot(element).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);

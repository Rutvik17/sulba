import { defineConfig, devices } from '@playwright/test';

const port = 4322;
const baseURL = `http://localhost:${port}`;
const isCI = Boolean(process.env.CI);

export default defineConfig({
  testDir: 'e2e',
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  reporter: isCI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL,
    trace: 'retain-on-failure',
    // Each test starts as a visitor who has answered "Don't allow", so the visit-count question
    // stays out of the way; analytics.spec.ts starts from a first visit.
    storageState: {
      cookies: [],
      origins: [{ origin: baseURL, localStorage: [{ name: 'sulba:analytics', value: 'deny' }] }],
    },
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'phone', use: { ...devices['Pixel 7'] } },
  ],
  // The built site served by workerd, the runtime Cloudflare uses in production.
  webServer: {
    command: `pnpm build && pnpm preview --port ${port}`,
    url: baseURL,
    reuseExistingServer: !isCI,
    timeout: 120_000,
    // A stand-in Web Analytics token, so the site asks to count visits as sulba.dev does. Tests
    // answer for Cloudflare's script, so nothing is ever counted.
    env: { PUBLIC_WEB_ANALYTICS_TOKEN: 'e2e-analytics-token' },
  },
});

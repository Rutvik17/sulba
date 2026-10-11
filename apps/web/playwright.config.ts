import { defineConfig, devices } from '@playwright/test';

const port = 4322;
const isCI = Boolean(process.env.CI);

export default defineConfig({
  testDir: 'e2e',
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  reporter: isCI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: `http://localhost:${port}`,
    trace: 'retain-on-failure',
  },
  // The three browser engines on a desktop, and the two that phones run.
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'chromium phone', use: { ...devices['Pixel 7'] } },
    { name: 'webkit phone', use: { ...devices['iPhone 15'] } },
  ],
  // The built site served by workerd, the runtime Cloudflare uses in production.
  webServer: {
    command: `pnpm build && pnpm preview --port ${port}`,
    url: `http://localhost:${port}`,
    reuseExistingServer: !isCI,
    timeout: 120_000,
  },
});

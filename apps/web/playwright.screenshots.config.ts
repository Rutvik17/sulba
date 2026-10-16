import { fileURLToPath } from 'node:url';
import { defineConfig, devices } from '@playwright/test';

// Screenshot tests compare the gallery with pictures committed beside them. Browsers draw text a
// little differently on every system, so these run only on Linux, in the Playwright image that CI
// uses; CONTRIBUTING.md says how to take new ones.
if (process.platform !== 'linux') {
  throw new Error("Screenshot tests run in CI, in Playwright's Linux image. See CONTRIBUTING.md.");
}

const port = 4323;

export default defineConfig({
  testDir: 'screenshots',
  snapshotPathTemplate: '{testDir}/{testFileName}-snapshots/{arg}-{projectName}{ext}',
  forbidOnly: true,
  reporter: [['github'], ['html', { open: 'never', outputFolder: 'screenshot-report' }]],
  expect: {
    toHaveScreenshot: {
      stylePath: fileURLToPath(new URL('screenshots/screenshot.css', import.meta.url)),
    },
  },
  use: {
    baseURL: `http://localhost:${port}`,
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'phone', use: { ...devices['Pixel 7'] } },
  ],
  // The gallery reads no course, so the site is built from the content package's fixture course,
  // as for the end-to-end tests, and its build doesn't grow with the courses' figures.
  webServer: {
    command: `pnpm build && pnpm preview --port ${port}`,
    url: `http://localhost:${port}`,
    env: { SULBA_GALLERY: 'on', SULBA_COURSES: '../../packages/content/fixtures/courses' },
    timeout: 120_000,
  },
});

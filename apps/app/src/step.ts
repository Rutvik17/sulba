// The step a team adds to a GitHub Actions job to send its test results to Sulba (decision record
// 50), and how each test runner writes the JUnit XML report it sends. Each runner's option is the
// one its own documentation gives.

export interface Runner {
  readonly id: string;
  readonly name: string;
  /** How the job runs the tests so they write a report. */
  readonly command: string;
  /** Where the report is: one file, or a pattern for one file a test class. */
  readonly report: string;
  /** What the job needs first, if anything. */
  readonly needs?: string;
}

export const runners: readonly Runner[] = [
  { id: 'pytest', name: 'pytest', command: 'pytest --junit-xml=junit.xml', report: 'junit.xml' },
  {
    id: 'vitest',
    name: 'Vitest',
    command: 'npx vitest run --reporter=junit --outputFile=junit.xml',
    report: 'junit.xml',
  },
  {
    id: 'jest',
    name: 'Jest',
    command: 'npx jest --ci --reporters=default --reporters=jest-junit',
    report: 'junit.xml',
    needs: 'jest-junit, added with npm install --save-dev jest-junit',
  },
  {
    id: 'playwright',
    name: 'Playwright',
    command: 'PLAYWRIGHT_JUNIT_OUTPUT_NAME=junit.xml npx playwright test --reporter=junit',
    report: 'junit.xml',
  },
  {
    id: 'go',
    name: 'Go',
    command: 'go run gotest.tools/gotestsum@v1.13.0 --junitfile junit.xml',
    report: 'junit.xml',
  },
  { id: 'maven', name: 'Maven', command: 'mvn test', report: 'target/surefire-reports/TEST-*.xml' },
];

/** Who the run's token is made out to, as /api/results checks it. */
export const audience = 'https://sulba.dev';

/** The address a report goes to. */
export function resultsAddress(origin: string, workspace: string, suite: string): string {
  return `${origin}/api/results?workspace=${workspace}&suite=${encodeURIComponent(suite)}`;
}

/**
 * The step, as YAML to paste after the step that runs the tests. It runs even when tests fail,
 * asks GitHub for the run's token made out to sulba.dev, and sends the report with it.
 */
export function workflowStep(origin: string, workspace: string, suite: string, runner: Runner) {
  const address = resultsAddress(origin, workspace, suite);
  const many = runner.report.includes('*');
  const send = many
    ? [
        `files=(); for f in ${runner.report}; do files+=(-F "report=@$f"); done`,
        `curl -sS --fail-with-body -H "Authorization: Bearer $token" "\${files[@]}" \\`,
        `  "${address}"`,
      ]
    : [
        `curl -sS --fail-with-body -H "Authorization: Bearer $token" \\`,
        `  -H "Content-Type: application/xml" --data-binary @${runner.report} \\`,
        `  "${address}"`,
      ];
  return [
    '- name: Send test results to Sulba',
    // biome-ignore lint/suspicious/noTemplateCurlyInString: a GitHub Actions expression, kept as written.
    '  if: ${{ !cancelled() }}',
    '  shell: bash',
    '  run: |',
    '    token=$(curl -sS -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \\',
    `      "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=${encodeURIComponent(audience)}" \\`,
    `      | sed -E 's/.*"value"[[:space:]]*:[[:space:]]*"([^"]+)".*/\\1/')`,
    ...send.map((line) => `    ${line}`),
  ].join('\n');
}

/** The job's permissions: reading the code, and asking for the run's token. */
export const permissions = ['permissions:', '  contents: read', '  id-token: write'].join('\n');

import { expect, test } from 'vitest';
import { resultsAddress, runners, workflowStep } from './step';

const runner = (id: string) => {
  const found = runners.find((each) => each.id === id);
  if (!found) throw new Error(id);
  return found;
};

test('the address names the workspace and the suite', () => {
  expect(resultsAddress('https://sulba.dev', 'acme', 'unit tests')).toBe(
    'https://sulba.dev/api/results?workspace=acme&suite=unit%20tests',
  );
});

test('the step asks for a token made out to sulba.dev and sends one report as XML', () => {
  expect(workflowStep('https://sulba.dev', 'acme', 'unit', runner('pytest'))).toBe(
    [
      '- name: Send test results to Sulba',
      // biome-ignore lint/suspicious/noTemplateCurlyInString: a GitHub Actions expression, kept as written.
      '  if: ${{ !cancelled() }}',
      '  shell: bash',
      '  run: |',
      '    token=$(curl -sS -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \\',
      '      "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=https%3A%2F%2Fsulba.dev" \\',
      `      | sed -E 's/.*"value"[[:space:]]*:[[:space:]]*"([^"]+)".*/\\1/')`,
      '    curl -sS --fail-with-body -H "Authorization: Bearer $token" \\',
      '      -H "Content-Type: application/xml" --data-binary @junit.xml \\',
      '      "https://sulba.dev/api/results?workspace=acme&suite=unit"',
    ].join('\n'),
  );
});

test('a runner that writes a file for each test class sends them all as one report', () => {
  const step = workflowStep('https://sulba.dev', 'acme', 'unit', runner('maven'));

  expect(step).toContain(
    'files=(); for f in target/surefire-reports/TEST-*.xml; do files+=(-F "report=@$f"); done',
  );
  // biome-ignore lint/suspicious/noTemplateCurlyInString: a bash array, kept as written.
  expect(step).toContain('"${files[@]}"');
  expect(step).not.toContain('--data-binary');
});

test('the token is made out to sulba.dev wherever the app is served', () => {
  expect(workflowStep('http://127.0.0.1:4321', 'acme', 'unit', runner('go'))).toContain(
    'audience=https%3A%2F%2Fsulba.dev',
  );
});

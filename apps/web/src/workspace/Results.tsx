import type { RunResult, TestResult } from '@sulba/lab/protocol';
import { classes } from '@sulba/ui/classes';
import styles from './results.module.css';

const css = classes(
  styles,
  'results',
  'note',
  'summary',
  'problem',
  'tests',
  'test',
  'pass',
  'fail',
  'name',
  'detail',
  'values',
  'where',
  'output',
);

export type Run =
  | { readonly state: 'idle' }
  | { readonly state: 'running' }
  | { readonly state: 'done'; readonly result: RunResult }
  /** Python or a package didn't load. */
  | { readonly state: 'failed' };

interface Props {
  readonly run: Run;
  readonly loading: boolean;
  /** Puts the cursor on a line of the learner's file. */
  readonly onGoTo: (line: number) => void;
  readonly file: string;
}

function summaryOf(result: RunResult): string {
  if (result.problem?.kind === 'TimeLimit') {
    return 'The tests were stopped after 5 seconds. A loop that never ends is the usual cause.';
  }
  if (result.problem) return 'The tests couldn’t run: your code has an error.';
  const passed = result.tests.filter((test) => test.status === 'pass').length;
  const all = result.tests.length;
  if (all === 1) return passed ? 'The test passes.' : 'The test fails.';
  return passed === all ? `All ${all} tests pass.` : `${passed} of ${all} tests pass.`;
}

function Where({ line, file, onGoTo }: { line: number; file: string; onGoTo: Props['onGoTo'] }) {
  return (
    <button type="button" className={css.where} onClick={() => onGoTo(line)}>
      {file}, line {line}
    </button>
  );
}

function Test({ test, file, onGoTo }: { test: TestResult; file: string; onGoTo: Props['onGoTo'] }) {
  const passed = test.status === 'pass';
  return (
    <li className={`${css.test} ${passed ? css.pass : css.fail}`}>
      <span className={css.name}>
        <span role="img" aria-label={passed ? 'Passed' : 'Failed'}>
          {passed ? '✓' : '✗'}
        </span>{' '}
        {test.name}
      </span>
      {!passed && (
        <div className={css.detail}>
          {test.message && <p>{test.message}</p>}
          {test.expected !== null && test.actual !== null && (
            <dl className={css.values}>
              <dt>Expected</dt>
              <dd>{test.expected}</dd>
              <dt>Got</dt>
              <dd>{test.actual}</dd>
            </dl>
          )}
          {test.location?.file === file && (
            <Where line={test.location.line} file={file} onGoTo={onGoTo} />
          )}
        </div>
      )}
    </li>
  );
}

/** The Tests tab: what the last run found, one line per test. */
export function TestResults({ run, loading, onGoTo, file }: Props) {
  return (
    <div className={css.results}>
      <p className={css.summary} aria-live="polite">
        {run.state === 'idle' && 'Run the tests to check your code.'}
        {run.state === 'running' && (loading ? 'Loading Python…' : 'Running the tests…')}
        {run.state === 'failed' &&
          'Python didn’t load. Check your connection, then run the tests again.'}
        {run.state === 'done' && summaryOf(run.result)}
      </p>
      {run.state === 'done' && run.result.problem && run.result.problem.kind !== 'TimeLimit' && (
        <div className={css.problem}>
          <p>
            {run.result.problem.kind}: {run.result.problem.message}
          </p>
          {run.result.problem.location?.file === file && (
            <Where line={run.result.problem.location.line} file={file} onGoTo={onGoTo} />
          )}
        </div>
      )}
      {run.state === 'done' && run.result.tests.length > 0 && (
        <ol className={css.tests}>
          {run.result.tests.map((test) => (
            <Test key={test.id ?? test.name} test={test} file={file} onGoTo={onGoTo} />
          ))}
        </ol>
      )}
    </div>
  );
}

/** The Printed tab: what the code printed, as it loaded and in each test. */
export function Printed({ run }: { run: Run }) {
  if (run.state !== 'done') {
    return <p className={css.note}>What your code prints while the tests run appears here.</p>;
  }
  const parts = [
    ...(run.result.output ? [{ name: 'While loading', text: run.result.output }] : []),
    ...run.result.tests
      .filter((test) => test.output)
      .map(({ name, output }) => ({ name, text: output })),
  ];
  if (parts.length === 0) return <p className={css.note}>Your code printed nothing.</p>;
  return (
    <div className={css.results}>
      {parts.map(({ name, text }) => (
        <section key={name}>
          <h3 className={css.name}>{name}</h3>
          <pre className={css.output}>{text}</pre>
        </section>
      ))}
    </div>
  );
}

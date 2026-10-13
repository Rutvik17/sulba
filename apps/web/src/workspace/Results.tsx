import type { RunResult, TestResult } from '@sulba/lab/protocol';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import type { ProblemView, ShipCheckView } from '../lib/labs';
import styles from './results.module.css';
import type { Review } from './stages';

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
  'group',
  'finish',
  'actions',
  'failure',
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

/** Why a run gave no results, or null if it gave them. */
function stoppedOf(result: RunResult): string | null {
  if (result.problem?.kind === 'TimeLimit') {
    return 'The tests were stopped after 5 seconds. A loop that never ends is the usual cause.';
  }
  if (result.problem) return 'The tests couldn’t run: your code has an error.';
  return null;
}

const passing = (tests: readonly TestResult[]) =>
  tests.filter((test) => test.status === 'pass').length;

/** How many of some tests or checks pass, such as "All 3 tests pass." */
function counted(tests: readonly TestResult[], one: string, many: string): string {
  const passed = passing(tests);
  if (tests.length === 1) return `The ${one} ${passed ? 'passes' : 'fails'}.`;
  return passed === tests.length
    ? `All ${tests.length} ${many} pass.`
    : `${passed} of ${tests.length} ${many} pass.`;
}

function summaryOf(result: RunResult): string {
  return stoppedOf(result) ?? counted(result.tests, 'test', 'tests');
}

/** A Catch run: how many production checks pass, then how the assistant's own tests did. */
function catchSummaryOf(
  result: RunResult,
  own: readonly TestResult[],
  checks: readonly TestResult[],
): string {
  const stopped = stoppedOf(result);
  if (stopped) return stopped;
  const checked =
    checks.length === 1
      ? `The production check ${passing(checks) ? 'passes' : 'fails'}.`
      : `${passing(checks)} of ${checks.length} production checks pass.`;
  const tested =
    passing(own) === own.length
      ? `The assistant’s ${own.length === 1 ? 'test passes' : 'tests pass'}.`
      : `${passing(own)} of the assistant’s ${own.length} tests pass.`;
  return `${checked} ${tested}`;
}

/** A Ship run: how its tests did, then its checks before it ships. */
function shipSummaryOf(
  result: RunResult,
  tests: readonly TestResult[],
  checks: readonly TestResult[],
): string {
  return (
    stoppedOf(result) ?? `${counted(tests, 'test', 'tests')} ${counted(checks, 'check', 'checks')}`
  );
}

/** The problem that stopped a run, with a link to its line when it's in the learner's file. */
function Stopped({ run, file, onGoTo }: Pick<Props, 'run' | 'file' | 'onGoTo'>) {
  if (run.state !== 'done' || !run.result.problem || run.result.problem.kind === 'TimeLimit') {
    return null;
  }
  const { problem } = run.result;
  return (
    <div className={css.problem}>
      <p>
        {problem.kind}: {problem.message}
      </p>
      {problem.location?.file === file && (
        <Where line={problem.location.line} file={file} onGoTo={onGoTo} />
      )}
    </div>
  );
}

function Mark({ passed }: { passed: boolean }) {
  return (
    <span role="img" aria-label={passed ? 'Passed' : 'Failed'}>
      {passed ? '✓' : '✗'}
    </span>
  );
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
        <Mark passed={passed} /> {test.name}
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
      <Stopped run={run} file={file} onGoTo={onGoTo} />
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

/** A line of a stage's text, made from its Markdoc when the site was built. */
export function Line({ html }: { html: string }) {
  // biome-ignore lint/security/noDangerouslySetInnerHtml: Markdoc made this HTML at build time from course files, which can't contain HTML of their own.
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

interface ShipProps extends Props {
  readonly checks: readonly ShipCheckView[];
}

/**
 * A Ship stage's Tests tab: each test by name, passed or not, and nothing of what it checked. Then
 * the checks before it ships, each with what it requires, why it failed and what it measured.
 */
export function ShipResults({ run, loading, onGoTo, file, checks }: ShipProps) {
  const ids = new Set(checks.map(({ check }) => check));
  const result = run.state === 'done' ? run.result : null;
  const ran = result?.problem ? [] : (result?.tests ?? []);
  const tests = ran.filter((test) => !test.id || !ids.has(test.id));
  const checked = ran.filter((test) => test.id !== null && ids.has(test.id));
  return (
    <div className={css.results}>
      <p className={css.summary} aria-live="polite">
        {run.state === 'idle' && 'Run the tests to check your code.'}
        {run.state === 'running' && (loading ? 'Loading Python…' : 'Running the tests…')}
        {run.state === 'failed' &&
          'Python didn’t load. Check your connection, then run the tests again.'}
        {result && shipSummaryOf(result, tests, checked)}
      </p>
      <Stopped run={run} file={file} onGoTo={onGoTo} />
      {tests.length > 0 && (
        <section>
          <h3 className={css.group}>Tests</h3>
          <ol className={css.tests}>
            {tests.map((test) => (
              <li
                key={test.id ?? test.name}
                className={`${css.test} ${test.status === 'pass' ? css.pass : css.fail}`}
              >
                <span className={css.name}>
                  <Mark passed={test.status === 'pass'} /> {test.name}
                </span>
              </li>
            ))}
          </ol>
        </section>
      )}
      <section>
        <h3 className={css.group}>Before it ships</h3>
        <ol className={css.tests}>
          {checks.map(({ check, title, requires, failure }) => {
            const test = checked.find((each) => each.id === check);
            const passed = test?.status === 'pass';
            return (
              <li
                key={check}
                className={test ? `${css.test} ${passed ? css.pass : css.fail}` : css.test}
              >
                <span className={css.name}>
                  {test && <Mark passed={passed} />} <Line html={title} />
                </span>
                <div className={css.detail}>
                  <p>
                    <Line html={requires} />
                  </p>
                  {test && !passed && (
                    <p className={css.failure}>
                      <Line html={failure} />
                    </p>
                  )}
                  {test?.note && <p>{test.note}</p>}
                </div>
              </li>
            );
          })}
        </ol>
      </section>
    </div>
  );
}

interface CatchProps extends Props {
  readonly problems: readonly ProblemView[];
  /** The finished review, or null while the learner is still reviewing. */
  readonly review: Review | null;
  /** The learner chose Finish review and is asked to confirm. */
  readonly confirming: boolean;
  /** Runs the tests on the code as it is and keeps the production checks it passes. */
  readonly onConfirm: () => void;
  readonly onCancel: () => void;
  /** A run is under way, or Python isn't ready, so the review can't finish yet. */
  readonly busy: boolean;
}

/**
 * A Catch stage's Tests tab: the assistant's own tests, one line each, and the production checks.
 * Until the review is finished, the checks are only a count; then each is named by its problem.
 */
export function CatchResults({
  run,
  loading,
  onGoTo,
  file,
  problems,
  review,
  confirming,
  onConfirm,
  onCancel,
  busy,
}: CatchProps) {
  const ids = new Set(problems.map((problem) => problem.check));
  const result = run.state === 'done' ? run.result : null;
  const tests = result?.problem ? [] : (result?.tests ?? []);
  const own = tests.filter((test) => !test.id || !ids.has(test.id));
  const checks = tests.filter((test) => test.id !== null && ids.has(test.id));
  const passed = (check: string) =>
    checks.length
      ? checks.some((test) => test.id === check && test.status === 'pass')
      : (review?.caught.includes(check) ?? false);
  return (
    <div className={css.results}>
      <p className={css.summary} aria-live="polite">
        {run.state === 'idle' && 'Run the tests to check the code.'}
        {run.state === 'running' && (loading ? 'Loading Python…' : 'Running the tests…')}
        {run.state === 'failed' &&
          'Python didn’t load. Check your connection, then run the tests again.'}
        {result && catchSummaryOf(result, own, checks)}
      </p>
      {confirming && !review && (
        <div className={css.finish}>
          <p>Finish the review? The production checks your code passes now become your score.</p>
          <div className={css.actions}>
            <Button size="small" autoFocus isDisabled={busy} onPress={onConfirm}>
              Finish review
            </Button>
            <Button size="small" variant="ghost" onPress={onCancel}>
              Keep reviewing
            </Button>
          </div>
        </div>
      )}
      <Stopped run={run} file={file} onGoTo={onGoTo} />
      {own.length > 0 && (
        <section>
          <h3 className={css.group}>The assistant’s tests</h3>
          <ol className={css.tests}>
            {own.map((test) => (
              <Test key={test.id ?? test.name} test={test} file={file} onGoTo={onGoTo} />
            ))}
          </ol>
        </section>
      )}
      <section>
        <h3 className={css.group}>Production checks</h3>
        {review ? (
          <ol className={css.tests}>
            {problems.map(({ check, title }) => (
              <li key={check} className={`${css.test} ${passed(check) ? css.pass : css.fail}`}>
                <span className={css.name}>
                  <Mark passed={passed(check)} /> {title}
                </span>
              </li>
            ))}
          </ol>
        ) : (
          <p className={css.note}>
            They test the code as it will really be used. Finish the review to see each one.
          </p>
        )}
      </section>
    </div>
  );
}

/**
 * The Printed tab: what the code printed, as it loaded and in each test. A hidden check's output
 * doesn't name the check. A Ship stage's tests are hidden whole, so only what the code printed as
 * it loaded shows.
 */
export function Printed({
  run,
  hidden = new Set(),
  loadingOnly = false,
}: {
  run: Run;
  hidden?: ReadonlySet<string>;
  loadingOnly?: boolean;
}) {
  if (run.state !== 'done') {
    return (
      <p className={css.note}>
        {loadingOnly
          ? 'What your code prints as it loads appears here. What it prints in the tests stays hidden.'
          : 'What your code prints while the tests run appears here.'}
      </p>
    );
  }
  const parts = [
    ...(run.result.output ? [{ name: 'While loading', text: run.result.output }] : []),
    ...(loadingOnly ? [] : run.result.tests)
      .filter((test) => test.output)
      .map(({ id, name, output }) => ({
        name: id !== null && hidden.has(id) ? 'A production check' : name,
        text: output,
      })),
  ];
  if (parts.length === 0) {
    return (
      <p className={css.note}>
        {loadingOnly ? 'Your code printed nothing as it loaded.' : 'Your code printed nothing.'}
      </p>
    );
  }
  return (
    <div className={css.results}>
      {parts.map(({ name, text }, index) => (
        // Hidden checks share a name, so the place in the run tells them apart.
        // biome-ignore lint/suspicious/noArrayIndexKey: the list is rebuilt whole after each run.
        <section key={`${index}-${name}`}>
          <h3 className={css.name}>{name}</h3>
          <pre className={css.output}>{text}</pre>
        </section>
      ))}
    </div>
  );
}

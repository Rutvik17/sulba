import type { Event } from '@sulba/data/outbox';
import type { Passed } from '@sulba/data/sync';
import { Editor, type EditorHandle } from '@sulba/editor/editor';
import { Lab } from '@sulba/lab/client';
import { pyodidePath, type RunResult } from '@sulba/lab/protocol';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Tab, TabList, TabPanel, Tabs } from '@sulba/ui/tabs';
import { useCallback, useEffect, useId, useRef, useState } from 'react';
import type { LabView, ProblemView, StageView } from '../lib/labs';
import { keyboardScrollBoxes } from '../lib/scroll-boxes';
import { ChartPanel } from './ChartPanel';
import { labData } from './data';
import { CatchResults, Line, Output, type Run, ShipResults, TestResults } from './Results';
import { codeOf, isOpen, packagesOf, type Review, runOf } from './stages';
import { type Stopwatch, stopwatch } from './stopwatch';
import { kept } from './storage';
import { type Recorder, startSync } from './sync';
import styles from './workspace.module.css';

const css = classes(
  styles,
  'stages',
  'stage',
  'number',
  'kind',
  'state',
  'workspace',
  'left',
  'panel',
  'builds',
  'prose',
  'hints',
  'right',
  'head',
  'file',
  'tools',
  'code',
  'dock',
  'done',
  'reviewed',
  'note',
  'problems',
  'caught',
  'missed',
);

const kinds: Record<StageView['kind'], string> = { build: 'Build', catch: 'Catch', ship: 'Ship' };

/** The stage to open: the one the address names if it's open, else the first not yet passed. */
function firstStage(lab: LabView): number {
  const named = new URLSearchParams(location.search).get('stage');
  const index = lab.stages.findIndex((stage) => stage.slug === named);
  if (index >= 0 && isOpen(lab, index, kept)) return index;
  const next = lab.stages.findIndex((stage) => !kept.passed(stage.id));
  return next >= 0 ? next : lab.stages.length - 1;
}

/** Each finished Catch review this browser kept, by stage id. */
function reviewsOf(lab: LabView): Record<string, Review> {
  const found: Record<string, Review> = {};
  for (const stage of lab.stages) {
    const review = stage.kind === 'catch' ? kept.review(stage.id) : null;
    if (review) found[stage.id] = review;
  }
  return found;
}

/** Keeps in this browser the stages passed in the learner's account, with their reviews. */
function takeIn(lab: LabView, passed: readonly Passed[]) {
  for (const { stageId, caught, problems } of passed) {
    const stage = lab.stages.find((each) => each.id === stageId);
    if (!stage) continue;
    if (stage.kind === 'catch' && caught && problems !== null && !kept.review(stage.id)) {
      kept.finish(stage.id, { caught, total: problems });
    } else if (!kept.passed(stage.id)) {
      kept.pass(stage.id);
    }
  }
}

/** A stage's pass, with its review when it's a Catch stage. */
function passOf(stage: StageView, review: Review | null): Event {
  return {
    kind: 'pass',
    review:
      stage.kind === 'catch' && review ? { caught: review.caught, problems: review.total } : null,
  };
}

/** A run's tests and, in a Catch or Ship stage, its checks, counted apart. */
function runEventOf(stage: StageView, result: RunResult): Event {
  const ids = new Set([
    ...stage.problems.map((problem) => problem.check),
    ...stage.shipChecks.map((check) => check.check),
  ]);
  const isCheck = (test: RunResult['tests'][number]) => test.id !== null && ids.has(test.id);
  const count = (tests: RunResult['tests']) => ({
    passed: tests.filter((test) => test.status === 'pass').length,
    total: tests.length,
  });
  return {
    kind: 'run',
    tests: count(result.tests.filter((test) => !isCheck(test))),
    checks: ids.size > 0 ? count(result.tests.filter(isCheck)) : null,
  };
}

/** A Catch run's review: the problems whose checks the code passed. */
function reviewOf(problems: readonly ProblemView[], result: RunResult): Review {
  const caught = problems.filter((problem) =>
    result.tests.some((test) => test.id === problem.check && test.status === 'pass'),
  );
  return { caught: caught.map((problem) => problem.check), total: problems.length };
}

/** A lab's stages, and the workspace for the one open. Python stays loaded across stages. */
export default function Workspace({ lab }: { lab: LabView }) {
  const [index, setIndex] = useState(() => firstStage(lab));
  const [passed, setPassed] = useState(() => lab.stages.filter((stage) => kept.passed(stage.id)));
  const [reviews, setReviews] = useState(() => reviewsOf(lab));
  const [python, setPython] = useState<Lab | null>(null);
  const [loading, setLoading] = useState(true);
  const recorder = useRef<Recorder | null>(null);

  // While the learner is signed in, stages they passed on another device open here too, and the
  // passes only this browser has go to their account.
  useEffect(() => {
    const sync = startSync((remote) => {
      takeIn(lab, remote);
      setPassed(lab.stages.filter((each) => kept.passed(each.id)));
      setReviews(reviewsOf(lab));
      const known = new Set(remote.map((each) => each.stageId));
      for (const stage of lab.stages) {
        if (kept.passed(stage.id) && !known.has(stage.id)) {
          sync.record(stage, passOf(stage, kept.review(stage.id)), 0);
        }
      }
    });
    recorder.current = sync;
    return () => sync.stop();
  }, [lab]);

  useEffect(() => {
    const runner = new Lab({ indexURL: pyodidePath });
    setPython(runner);
    return () => runner.dispose();
  }, []);

  // The lab's data comes while Python loads, so the first run doesn't wait for it. A run that
  // finds it missing fetches it again.
  useEffect(() => {
    labData(lab).catch(() => undefined);
  }, [lab]);

  // Each stage loads the packages it needs when it opens, so an early stage never waits for a
  // later stage's. A run tries again and says so if Python still won't load.
  useEffect(() => {
    if (!python) return;
    let current = true;
    const done = () => {
      if (current) setLoading(false);
    };
    setLoading(true);
    python.prepare(packagesOf(lab, index)).then(done, done);
    return () => {
      current = false;
    };
  }, [python, lab, index]);

  const open = (to: number) => {
    setIndex(to);
    const address = new URL(location.href);
    address.searchParams.set('stage', lab.stages[to]?.slug ?? '');
    history.replaceState(null, '', address);
  };

  const stage = lab.stages[index];
  if (!stage) return null;
  const isPassed = (each: StageView) => passed.some((done) => done.id === each.id);
  const stateOf = (each: StageView, at: number) => {
    const review = reviews[each.id];
    if (review) return `${review.caught.length} of ${review.total} caught`;
    if (isPassed(each)) return 'Done';
    return isOpen(lab, at, kept) ? '' : `Opens when stage ${at} is done`;
  };

  return (
    <>
      <nav aria-label="Stages">
        <ol className={css.stages}>
          {lab.stages.map((each, at) => (
            <li key={each.id}>
              <button
                type="button"
                className={css.stage}
                aria-current={at === index ? 'step' : undefined}
                disabled={!isOpen(lab, at, kept)}
                onClick={() => open(at)}
              >
                <span className={css.number}>{at + 1}</span>
                <span className={css.kind}>{kinds[each.kind]}</span>
                {each.title}
                <span className={css.state}>{stateOf(each, at)}</span>
              </button>
            </li>
          ))}
        </ol>
      </nav>
      <StageWorkspace
        key={stage.id}
        lab={lab}
        index={index}
        python={python}
        loading={loading}
        passed={isPassed(stage)}
        review={reviews[stage.id] ?? null}
        onPass={() => {
          kept.pass(stage.id);
          setPassed(lab.stages.filter((each) => kept.passed(each.id)));
        }}
        onFinish={(review) => {
          kept.finish(stage.id, review);
          setReviews((before) => ({ ...before, [stage.id]: review }));
          setPassed(lab.stages.filter((each) => kept.passed(each.id)));
        }}
        onNext={index + 1 < lab.stages.length ? () => open(index + 1) : null}
        record={(event, seconds) => recorder.current?.record(stage, event, seconds)}
      />
    </>
  );
}

interface StageProps {
  readonly lab: LabView;
  readonly index: number;
  readonly python: Lab | null;
  readonly loading: boolean;
  readonly passed: boolean;
  /** A Catch stage's finished review, or null. */
  readonly review: Review | null;
  readonly onPass: () => void;
  /** Keeps a Catch stage's review, which passes the stage. */
  readonly onFinish: (review: Review) => void;
  readonly onNext: (() => void) | null;
  /** Keeps what the learner did, with the seconds since their last attempt in this stage. */
  readonly record: (event: Event, seconds: number) => void;
}

function StageWorkspace({
  lab,
  index,
  python,
  loading,
  passed,
  review,
  onPass,
  onFinish,
  onNext,
  record,
}: StageProps) {
  const stage = lab.stages[index] as StageView;
  const isCatch = stage.kind === 'catch';
  const isShip = stage.kind === 'ship';
  const editor = useRef<EditorHandle>(null);
  const left = useRef<HTMLDivElement>(null);
  const finished = useRef<HTMLParagraphElement>(null);
  const finishId = useId();
  const [opening] = useState(() => codeOf(lab, index, kept));
  const code = useCallback(() => editor.current?.code() ?? opening, [opening]);
  const [run, setRun] = useState<Run>({ state: 'idle' });
  const [runs, setRuns] = useState(0);
  const [tried, setTried] = useState(passed);
  const [hints, setHints] = useState(0);
  const [tab, setTab] = useState('brief');
  const [results, setResults] = useState<'tests' | 'output'>('tests');
  const [confirming, setConfirming] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const watch = useRef<Stopwatch | null>(null);
  const viewedSolution = useRef(false);

  useEffect(() => {
    const each = stopwatch();
    watch.current = each;
    return () => each.stop();
  }, []);

  const lap = () => watch.current?.lap() ?? 0;

  // Once Finish review has kept the score, the score is where the learner's focus goes.
  useEffect(() => {
    if (review && finishing) finished.current?.focus();
  }, [review, finishing]);

  /** Runs the tests on the code in the editor, or returns null if they couldn't run. */
  const execute = async (): Promise<RunResult | null> => {
    if (!python || run.state === 'running') return null;
    setRun({ state: 'running' });
    setResults('tests');
    setTried(true);
    try {
      const result = await python.run(runOf(lab, await labData(lab), index, code(), kept));
      setRun({ state: 'done', result });
      setRuns((before) => before + 1);
      record(runEventOf(stage, result), lap());
      return result;
    } catch {
      setRun({ state: 'failed' });
      return null;
    }
  };

  // A Catch review finishes by itself once the code passes every test and check.
  const runTests = async () => {
    const result = await execute();
    if (result?.status !== 'pass') return;
    if (!isCatch) {
      if (!passed) record(passOf(stage, null), lap());
      onPass();
    } else if (!review) {
      const finished = reviewOf(stage.problems, result);
      onFinish(finished);
      record(passOf(stage, finished), lap());
    }
  };

  // The score is the code as it stands: the review finishes only on a run that gave results. A
  // run that couldn't give them leaves the question open, under the error.
  const finish = async () => {
    const result = await execute();
    if (!result || result.problem || result.tests.length === 0 || review) return;
    setFinishing(true);
    setConfirming(false);
    const finished = reviewOf(stage.problems, result);
    onFinish(finished);
    record(passOf(stage, finished), lap());
  };

  const askToFinish = () => {
    setResults('tests');
    setConfirming(true);
  };

  const keepReviewing = () => {
    setConfirming(false);
    document.getElementById(finishId)?.focus();
  };

  const show = (panel: string) => {
    setTab(panel);
    left.current?.scrollIntoView({ block: 'nearest' });
  };

  const reset = () => {
    const fresh = codeOf(lab, index, {
      ...kept,
      code: (id) => (id === stage.id ? null : kept.code(id)),
    });
    editor.current?.replace(fresh);
    kept.saveCode(stage.id, null);
  };

  const done = run.state === 'done' && run.result.status === 'pass';
  const solutionOpen = isCatch ? review !== null : tried;
  const unrevealed = new Set(review ? [] : stage.problems.map((problem) => problem.check));

  return (
    <section className={css.workspace} aria-label={`Stage ${index + 1}: ${stage.title}`}>
      <div className={css.left} ref={left}>
        <Tabs
          selectedKey={tab}
          onSelectionChange={(key) => {
            setTab(String(key));
            if (key === 'solution' && !viewedSolution.current) {
              viewedSolution.current = true;
              record({ kind: 'solution' }, lap());
            }
          }}
        >
          <TabList aria-label="Stage">
            <Tab id="brief">Brief</Tab>
            {stage.hints.length > 0 && <Tab id="hints">Hints</Tab>}
            <Tab id="explanation">Explanation</Tab>
            <Tab id="solution" isDisabled={!solutionOpen}>
              Solution
            </Tab>
            {stage.chart && <Tab id="chart">Chart</Tab>}
          </TabList>
          <TabPanel id="brief">
            <div className={css.panel}>
              <h2>{stage.title}</h2>
              <p className={css.builds}>
                <strong>Builds on</strong> · <Line html={stage.builds} />
              </p>
              <Prose html={stage.brief} />
            </div>
          </TabPanel>
          {stage.hints.length > 0 && (
            <TabPanel id="hints">
              <div className={css.panel}>
                {hints > 0 && (
                  <ol className={css.hints}>
                    {stage.hints.slice(0, hints).map((hint) => (
                      <li key={hint}>
                        <Prose html={hint} />
                      </li>
                    ))}
                  </ol>
                )}
                {hints < stage.hints.length ? (
                  <Button
                    variant="outline"
                    size="small"
                    onPress={() => {
                      setHints(hints + 1);
                      record({ kind: 'hint', hint: hints + 1 }, lap());
                    }}
                  >
                    {hints === 0 ? 'Show a hint' : 'Show the next hint'}
                  </Button>
                ) : (
                  <p>No more hints.</p>
                )}
              </div>
            </TabPanel>
          )}
          <TabPanel id="explanation">
            <div className={css.panel}>
              {isCatch && !review ? (
                <p className={css.note}>Opens when you finish the review.</p>
              ) : isShip && !tried ? (
                <p className={css.note}>Opens after your first run.</p>
              ) : (
                <Prose html={stage.explanation} />
              )}
              {isCatch && review && <Problems problems={stage.problems} review={review} />}
              {isCatch && review && stage.afterProblems !== null && (
                <Prose html={stage.afterProblems} />
              )}
            </div>
          </TabPanel>
          <TabPanel id="solution">
            <div className={css.panel}>
              <Editor defaultValue={stage.solution} label={`Solution: ${stage.file}`} readOnly />
            </div>
          </TabPanel>
          {stage.chart && (
            <TabPanel id="chart">
              <div className={css.panel}>
                <h2>{stage.chart.title}</h2>
                <ChartPanel
                  lab={lab}
                  index={index}
                  python={python}
                  passed={passed}
                  code={code}
                  runs={runs}
                />
              </div>
            </TabPanel>
          )}
        </Tabs>
      </div>

      <div className={css.right}>
        <div className={css.head}>
          <span className={css.file}>{stage.file}</span>
          <div className={css.tools}>
            <Button variant="ghost" size="small" onPress={reset}>
              Reset
            </Button>
            {isCatch && !review && (
              <Button
                id={finishId}
                variant="outline"
                size="small"
                onPress={askToFinish}
                isDisabled={!python || run.state === 'running'}
              >
                Finish review
              </Button>
            )}
            <Button size="small" onPress={runTests} isDisabled={!python || run.state === 'running'}>
              Run tests
            </Button>
          </div>
        </div>
        <div className={css.code}>
          <Editor
            ref={editor}
            defaultValue={opening}
            label={stage.file}
            onChange={(code) => kept.saveCode(stage.id, code)}
            onRun={runTests}
          />
        </div>
        <div className={css.dock}>
          {isCatch && review && (
            <div className={`${css.done} ${css.reviewed}`}>
              <p ref={finished} tabIndex={-1}>
                Review finished. You caught {review.caught.length} of {review.total} problems.
              </p>
              <div className={css.tools}>
                <Button variant="outline" size="small" onPress={() => show('explanation')}>
                  See each problem
                </Button>
                {onNext && (
                  <Button size="small" onPress={onNext}>
                    Next stage
                  </Button>
                )}
              </div>
            </div>
          )}
          {!isCatch && done && (
            <div className={css.done}>
              <p>Stage {index + 1} done.</p>
              <div className={css.tools}>
                {stage.chart && (
                  <Button variant="outline" size="small" onPress={() => show('chart')}>
                    See the chart
                  </Button>
                )}
                {onNext && (
                  <Button size="small" onPress={onNext}>
                    Next stage
                  </Button>
                )}
              </div>
            </div>
          )}
          <Tabs
            selectedKey={results}
            onSelectionChange={(key) => setResults(key as typeof results)}
          >
            <TabList aria-label="Results">
              <Tab id="tests">Tests</Tab>
              <Tab id="output">Output</Tab>
            </TabList>
            <TabPanel id="tests">
              <div className={css.panel}>
                {isCatch ? (
                  <CatchResults
                    run={run}
                    loading={loading}
                    file={stage.file}
                    onGoTo={(line) => editor.current?.goTo(line)}
                    problems={stage.problems}
                    review={review}
                    confirming={confirming}
                    onConfirm={finish}
                    onCancel={keepReviewing}
                    busy={!python || run.state === 'running'}
                  />
                ) : isShip ? (
                  <ShipResults
                    run={run}
                    loading={loading}
                    file={stage.file}
                    onGoTo={(line) => editor.current?.goTo(line)}
                    checks={stage.shipChecks}
                  />
                ) : (
                  <TestResults
                    run={run}
                    loading={loading}
                    file={stage.file}
                    onGoTo={(line) => editor.current?.goTo(line)}
                  />
                )}
              </div>
            </TabPanel>
            <TabPanel id="output">
              <div className={css.panel}>
                <Output run={run} hidden={unrevealed} loadingOnly={isShip} />
              </div>
            </TabPanel>
          </Tabs>
        </div>
      </div>
    </section>
  );
}

/** A finished review's problems: each one caught or missed, what it would cost, and its fix. */
function Problems({ problems, review }: { problems: readonly ProblemView[]; review: Review }) {
  return (
    <ol className={css.problems}>
      {problems.map((problem) => {
        const caught = review.caught.includes(problem.check);
        return (
          <li key={problem.check}>
            <h3>{problem.title}</h3>
            <p className={caught ? css.caught : css.missed}>{caught ? 'Caught' : 'Missed'}</p>
            <Prose html={problem.cost} />
            <Prose html={problem.fix} />
          </li>
        );
      })}
    </ol>
  );
}

/** Prose made from a course's Markdoc files when the site was built. */
function Prose({ html }: { html: string }) {
  const prose = useRef<HTMLDivElement>(null);
  // biome-ignore lint/correctness/useExhaustiveDependencies: html isn't read, but each new html puts new boxes in the page.
  useEffect(() => (prose.current ? keyboardScrollBoxes(prose.current) : undefined), [html]);
  return (
    <div
      ref={prose}
      className={css.prose}
      // biome-ignore lint/security/noDangerouslySetInnerHtml: Markdoc made this HTML at build time from course files, which can't contain HTML of their own.
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

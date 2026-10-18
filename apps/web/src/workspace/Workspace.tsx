import type { Event } from '@sulba/data/outbox';
import { Editor, type EditorHandle } from '@sulba/editor/editor';
import { Lab } from '@sulba/lab/client';
import { pyodidePath, type RunResult } from '@sulba/lab/protocol';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Tab, TabList, TabPanel, Tabs } from '@sulba/ui/tabs';
import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import type { LabView, ProblemView, StageView } from '../lib/labs';
import { ChartPanel } from './ChartPanel';
import { labData, projectFiles } from './data';
import MachineWorkspace from './MachineWorkspace';
import { clock, elapsed, type ProblemState, solvedIn } from './problem';
import { firstStage, passOf, reviewsOf, takeIn } from './progress';
import { CatchResults, Line, Output, type Run, ShipResults, TestResults } from './Results';
import { Problems, Prose, StageNav } from './StageParts';
import { codeOf, downloadOf, packagesOf, type Review, runOf } from './stages';
import { type Stopwatch, stopwatch } from './stopwatch';
import { kept } from './storage';
import { type Recorder, startSync } from './sync';
import styles from './workspace.module.css';

const css = classes(
  styles,
  'workspace',
  'left',
  'panel',
  'builds',
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
  'clock',
  'over',
  'plan',
  'start',
);

/**
 * A lab's stages, and the workspace for the one open: in this page, or for a lab that runs on the
 * learner's machine, how to run it there (decision record 28).
 */
export default function Workspace({ lab }: { lab: LabView }) {
  return lab.runs === 'machine' ? <MachineWorkspace lab={lab} /> : <BrowserWorkspace lab={lab} />;
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
function BrowserWorkspace({ lab }: { lab: LabView }) {
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

  return (
    <>
      <StageNav lab={lab} index={index} passed={passed} reviews={reviews} onOpen={open} />
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
  const isProblem = stage.kind === 'problem';
  const [problem, setProblem] = useState<ProblemState | null>(() =>
    isProblem ? kept.problem(stage.id) : null,
  );
  // A run's result keeps its time with the plan as it is then, which may have changed during it.
  const latest = useRef(problem);
  const keepProblem = (state: ProblemState) => {
    latest.current = state;
    setProblem(state);
    kept.saveProblem(stage.id, state);
  };
  // The clock runs until the problem is solved. One solved on another device kept no time here, so
  // it shows no clock.
  const now = useNow(problem !== null && problem.solved === null && !passed);
  const seconds = problem ? elapsed(problem, now) : 0;
  const timed = problem !== null && (problem.solved !== null || !passed);
  // A Problem stage shows its problem once the learner starts, and its code once their plan is
  // written. One passed on another device opens in full, with or without a start kept here.
  const started = !isProblem || passed || problem !== null;
  const coding = !isProblem || passed || problem?.coding === true;
  const explained = !isProblem || passed || seconds >= stage.minutes * 60;
  const editor = useRef<EditorHandle>(null);
  const left = useRef<HTMLDivElement>(null);
  const brief = useRef<HTMLDivElement>(null);
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

  // A Catch review finishes by itself once the code passes every test and check. A problem is
  // solved when the code that passes was run, not when its tests finish.
  const runTests = async () => {
    const ran = Date.now();
    const result = await execute();
    if (result?.status !== 'pass') return;
    if (!isCatch) {
      if (!passed) record(passOf(stage, null), lap());
      const state = latest.current;
      if (state && state.solved === null) keepProblem({ ...state, solved: elapsed(state, ran) });
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

  // A lab with a project downloads as one, with the code as it stands in this stage. The zip is
  // made here in the browser, by code loaded only for a download.
  const [downloadFailed, setDownloadFailed] = useState(false);
  const download = async () => {
    setDownloadFailed(false);
    try {
      const [data, project, { save, zipped }] = await Promise.all([
        labData(lab),
        projectFiles(lab),
        import('./download'),
      ]);
      const folder = lab.path.split('/').at(-1) ?? 'lab';
      save(`${folder}.zip`, zipped(folder, downloadOf(lab, data, index, code(), kept, project)));
    } catch {
      setDownloadFailed(true);
    }
  };

  const done = run.state === 'done' && run.result.status === 'pass';
  const solutionOpen = isCatch ? review !== null : isProblem ? explained : tried;
  // Starting shows the problem, and finishing the plan opens the code, so focus goes to each.
  const start = () => {
    flushSync(() => keepProblem({ started: Date.now(), plan: '', coding: false, solved: null }));
    brief.current?.focus();
  };
  const writeCode = (state: ProblemState) => {
    flushSync(() => keepProblem({ ...state, coding: true }));
    editor.current?.goTo(1);
  };
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
            {isProblem && coding && problem && <Tab id="plan">Plan</Tab>}
            {stage.hints.length > 0 && started && <Tab id="hints">Hints</Tab>}
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
              {started ? (
                <div ref={brief} tabIndex={-1}>
                  <Prose html={stage.brief} />
                </div>
              ) : (
                <div className={css.start}>
                  <p>
                    You have {stage.minutes} minutes from when you start. Plan first: how it works,
                    what it costs in time and space, and the inputs that could break it. Then write
                    the code.
                  </p>
                  <Button onPress={start}>Start</Button>
                </div>
              )}
            </div>
          </TabPanel>
          {isProblem && coding && problem && (
            <TabPanel id="plan">
              <div className={css.panel}>
                <Plan
                  plan={problem.plan}
                  onChange={(plan) => keepProblem({ ...problem, plan })}
                  onDone={null}
                />
              </div>
            </TabPanel>
          )}
          {stage.hints.length > 0 && started && (
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
              ) : !explained ? (
                <p className={css.note}>
                  Opens when you solve it, or when its {stage.minutes} minutes are up.
                </p>
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
          {timed && (
            <span
              role="timer"
              className={seconds > stage.minutes * 60 ? `${css.clock} ${css.over}` : css.clock}
            >
              {clock(seconds, stage.minutes)}
            </span>
          )}
          <div className={css.tools}>
            <Button variant="ghost" size="small" onPress={reset} isDisabled={!coding}>
              Reset
            </Button>
            {lab.project.length > 0 && (
              <Button variant="ghost" size="small" onPress={download} isDisabled={!coding}>
                Download
              </Button>
            )}
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
            <Button
              size="small"
              onPress={runTests}
              isDisabled={!python || run.state === 'running' || !coding}
            >
              Run tests
            </Button>
          </div>
        </div>
        {downloadFailed && (
          <p className={css.note} role="alert">
            The download failed. Try again.
          </p>
        )}
        <div className={css.code}>
          {coding ? (
            <Editor
              ref={editor}
              defaultValue={opening}
              label={stage.file}
              onChange={(code) => kept.saveCode(stage.id, code)}
              onRun={runTests}
            />
          ) : problem ? (
            <Plan
              plan={problem.plan}
              onChange={(plan) => keepProblem({ ...problem, plan })}
              onDone={() => writeCode(problem)}
            />
          ) : (
            <p className={css.note}>Your plan, then your code, go here once you start.</p>
          )}
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
              <p>
                {problem && problem.solved !== null
                  ? solvedIn(problem.solved, stage.minutes)
                  : `Stage ${index + 1} done.`}
              </p>
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

/** The time now, in milliseconds since 1970, kept current each second while `running`. */
function useNow(running: boolean): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!running) return;
    setNow(Date.now());
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [running]);
  return now;
}

/** A Problem stage's plan, which opens the code once it's written, then stays open to change. */
function Plan({
  plan,
  onChange,
  onDone,
}: {
  plan: string;
  onChange: (plan: string) => void;
  /** Opens the code, or null once the code is open. */
  onDone: (() => void) | null;
}) {
  const id = useId();
  return (
    <form
      className={css.plan}
      onSubmit={(event) => {
        event.preventDefault();
        onDone?.();
      }}
    >
      <label htmlFor={`${id}-plan`}>Your plan</label>
      <p id={`${id}-about`} className={css.note}>
        How it works, what it costs in time and space, and the inputs that could break it.
      </p>
      <textarea
        id={`${id}-plan`}
        aria-describedby={`${id}-about`}
        value={plan}
        onChange={(event) => onChange(event.target.value)}
      />
      {onDone && (
        <div>
          <Button type="submit" isDisabled={plan.trim() === ''}>
            Write the code
          </Button>
        </div>
      )}
    </form>
  );
}

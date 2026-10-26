import type { Event } from '@sulba/data/outbox';
import { Editor } from '@sulba/editor/editor';
import { languageOf } from '@sulba/editor/language';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Tab, TabList, TabPanel, Tabs } from '@sulba/ui/tabs';
import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchedOf, servedOf } from '../lib/lab-facts';
import type { LabView, StageView } from '../lib/labs';
import { labData, projectFiles } from './data';
import { type Report, reportOf } from './link';
import { firstStage, passOf, reviewsOf, takeIn } from './progress';
import { Line } from './Results';
import { Hints, Problems, Prose, StageNav } from './StageParts';
import { machineDownloadOf, type Review } from './stages';
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
  'right',
  'head',
  'file',
  'tools',
  'machine',
  'prose',
  'dock',
  'done',
  'reviewed',
  'note',
);

declare global {
  interface Window {
    /** The fragment of the link the page opened by, which the page's head took out of the address. */
    sulbaRun?: string;
  }
}

/** What a link from the learner's machine brought, and the stages it marked done here. */
interface Arrival {
  readonly report: Report;
  readonly done: readonly StageView[];
}

/**
 * Takes in a link from the learner's machine: the stages it marks done are kept in this browser,
 * and its fragment comes out of the address, so a reload or a shared address doesn't carry it again.
 */
function takeInLink(lab: LabView, fragment: string): Arrival | null {
  const report = reportOf(lab, fragment);
  if (location.hash.startsWith('#run=')) {
    history.replaceState(null, '', `${location.pathname}${location.search}`);
  }
  if (!report) return null;
  const done = lab.stages.filter((stage) => report.passed.has(stage.id) && !kept.passed(stage.id));
  for (const [id, review] of report.passed) {
    if (review && !kept.review(id)) kept.finish(id, review);
    else if (!kept.passed(id)) kept.pass(id);
  }
  return { report, done };
}

/** The link each lab's page opened by, taken in once however often the page first renders. */
const opened = new Map<string, Arrival | null>();

function openedBy(lab: LabView): Arrival | null {
  if (!opened.has(lab.id)) opened.set(lab.id, takeInLink(lab, window.sulbaRun ?? location.hash));
  return opened.get(lab.id) ?? null;
}

/**
 * The stage to open: the last one a link just marked done, whose explanation is what the learner
 * reads next, as after a pass in the browser; else the one the address names, or the first not
 * yet passed.
 */
function stageAfter(lab: LabView, arrival: Arrival | null): number {
  const last = arrival?.done.at(-1);
  return last ? lab.stages.indexOf(last) : firstStage(lab);
}

/** The stages' numbers in words, such as "1 and 2". */
function numbers(lab: LabView, stages: readonly StageView[]): string {
  const each = stages.map((stage) => String(lab.stages.indexOf(stage) + 1));
  return each.length > 1 ? `${each.slice(0, -1).join(', ')} and ${each.at(-1)}` : (each[0] ?? '');
}

/**
 * A lab that runs on the learner's machine (decision record 28): its stages, each one's brief,
 * hints, explanation and solution, the download and the commands that run it, and the stages done,
 * which the runner's links mark here.
 */
export default function MachineWorkspace({ lab }: { lab: LabView }) {
  const [arrival, setArrival] = useState(() => openedBy(lab));
  const [index, setIndex] = useState(() => stageAfter(lab, arrival));
  const [passed, setPassed] = useState(() => lab.stages.filter((stage) => kept.passed(stage.id)));
  const [reviews, setReviews] = useState(() => reviewsOf(lab));
  const recorder = useRef<Recorder | null>(null);
  // The stages whose passes came in a link, which sends them with its own attempts.
  const linked = useRef(new Set(arrival?.report.passed.keys()));
  const opening = useRef(arrival);

  const refresh = useCallback(() => {
    setPassed(lab.stages.filter((each) => kept.passed(each.id)));
    setReviews(reviewsOf(lab));
  }, [lab]);

  // Signed in, the attempts a link carries go to the learner's account, and stages done on
  // another device are done here too.
  useEffect(() => {
    const sync = startSync((remote) => {
      takeIn(lab, remote);
      refresh();
      const known = new Set(remote.map((each) => each.stageId));
      for (const stage of lab.stages) {
        if (kept.passed(stage.id) && !known.has(stage.id) && !linked.current.has(stage.id)) {
          sync.record(stage, passOf(stage, kept.review(stage.id)), 0);
        }
      }
    });
    if (opening.current) sync.takeIn(opening.current.report.attempts);
    recorder.current = sync;
    return () => sync.stop();
  }, [lab, refresh]);

  // A link pasted into this page's own address changes only its fragment, which doesn't load the
  // page again.
  useEffect(() => {
    const changed = () => {
      const next = takeInLink(lab, location.hash);
      if (!next) return;
      for (const id of next.report.passed.keys()) linked.current.add(id);
      recorder.current?.takeIn(next.report.attempts);
      setArrival(next);
      refresh();
      setIndex(stageAfter(lab, next));
    };
    addEventListener('hashchange', changed);
    return () => removeEventListener('hashchange', changed);
  }, [lab, refresh]);

  const open = (to: number) => {
    setIndex(to);
    const address = new URL(location.href);
    address.searchParams.set('stage', lab.stages[to]?.slug ?? '');
    history.replaceState(null, '', address);
  };

  const stage = lab.stages[index];
  if (!stage) return null;
  const notice =
    arrival && arrival.done.length > 0
      ? `${arrival.done.length > 1 ? 'Stages' : 'Stage'} ${numbers(lab, arrival.done)} done on your machine.`
      : null;

  return (
    <>
      <StageNav lab={lab} index={index} passed={passed} reviews={reviews} onOpen={open} />
      <MachineStage
        key={stage.id}
        lab={lab}
        index={index}
        passed={passed.some((each) => each.id === stage.id)}
        review={reviews[stage.id] ?? null}
        notice={notice}
        onNext={index + 1 < lab.stages.length ? () => open(index + 1) : null}
        record={(event, seconds) => recorder.current?.record(stage, event, seconds)}
      />
    </>
  );
}

interface StageProps {
  readonly lab: LabView;
  readonly index: number;
  readonly passed: boolean;
  /** A Catch stage's finished review, or null. */
  readonly review: Review | null;
  /** What the link the page opened by marked done, or null. */
  readonly notice: string | null;
  readonly onNext: (() => void) | null;
  /** Keeps what the learner did, with the seconds since their last attempt in this stage. */
  readonly record: (event: Event, seconds: number) => void;
}

/** A line of prose in plain words, as a terminal shows it. */
function plain(html: string): string {
  return new DOMParser().parseFromString(html, 'text/html').body.textContent ?? '';
}

function MachineStage({ lab, index, passed, review, notice, onNext, record }: StageProps) {
  const stage = lab.stages[index] as StageView;
  const isCatch = stage.kind === 'catch';
  const [tab, setTab] = useState('brief');
  const [hints, setHints] = useState(0);
  const [downloadFailed, setDownloadFailed] = useState(false);
  const watch = useRef<Stopwatch | null>(null);
  const viewedSolution = useRef(false);
  const left = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const each = stopwatch();
    watch.current = each;
    return () => each.stop();
  }, []);

  const lap = () => watch.current?.lap() ?? 0;

  // The download is made here in the browser, by code loaded only for a download.
  const download = async () => {
    setDownloadFailed(false);
    try {
      const [data, project, { save, zipped }] = await Promise.all([
        labData(lab),
        projectFiles(lab),
        import('./download'),
      ]);
      const folder = lab.path.split('/').at(-1) ?? 'lab';
      const page = `${location.origin}/${lab.path}/`;
      save(
        `${folder}.zip`,
        zipped(folder, machineDownloadOf(lab, data, kept, project, page, plain)),
      );
    } catch {
      setDownloadFailed(true);
    }
  };

  // A Catch stage's explanation and solution open with its review; another stage's solution is
  // there all along, since its runs are on the learner's machine.
  const solutionOpen = !isCatch || review !== null;
  const fetched = fetchedOf(lab);
  const served = servedOf(lab);
  const typeScript = lab.stages.some((each) => each.file.endsWith('.ts'));
  const go = lab.stages.some((each) => each.file.endsWith('.go'));
  const java = lab.stages.some((each) => each.file.endsWith('.java'));

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
                <Hints
                  hints={stage.hints}
                  shown={hints}
                  onShow={() => {
                    setHints(hints + 1);
                    record({ kind: 'hint', hint: hints + 1 }, lap());
                  }}
                />
              </div>
            </TabPanel>
          )}
          <TabPanel id="explanation">
            <div className={css.panel}>
              {isCatch && !review ? (
                <p className={css.note}>Opens when you finish the review.</p>
              ) : stage.kind === 'ship' && !passed ? (
                <p className={css.note}>Opens when the stage is done.</p>
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
              <Editor
                defaultValue={stage.solution}
                label={`Solution: ${stage.file}`}
                language={languageOf(stage.file)}
                readOnly
              />
            </div>
          </TabPanel>
        </Tabs>
      </div>

      <div className={css.right}>
        <div className={css.head}>
          <span className={css.file}>{stage.file}</span>
          <div className={css.tools}>
            <Button size="small" onPress={download}>
              Download
            </Button>
          </div>
        </div>
        {downloadFailed && (
          <p className={css.note} role="alert">
            The download failed. Try again.
          </p>
        )}
        <div className={`${css.machine} ${css.prose}`}>
          {notice && <p role="status">{notice}</p>}
          <p>
            This lab runs on your machine, in a folder you download once. Install{' '}
            <a href="https://docs.astral.sh/uv/">uv</a>, download the lab, unzip it, and in its
            folder run:
          </p>
          <pre>
            <code>uv run sulba.py</code>
          </pre>
          <p>
            It runs the tests of the stage you’re on. When the stage is done, it opens a link back
            to this page that marks it done here, and <code>uv run sulba.py next</code> starts the
            next stage.
          </p>
          {fetched && (
            <p>
              The first time, it also downloads the files the lab needs into <code>data</code>:{' '}
              {fetched.size}, from {fetched.hosts}.
            </p>
          )}
          {served && served.count === 1 && (
            <p>
              <code>uv run sulba.py model</code> starts the lab’s model, {served.titles}, on your
              machine, where your code can call it by that name at{' '}
              <code>http://127.0.0.1:9931/v1</code>. The first time, it downloads the model,{' '}
              {served.size}, from {served.hosts}, and llama.cpp’s server for your system, from
              github.com.
            </p>
          )}
          {served && served.count > 1 && (
            <p>
              <code>uv run sulba.py model</code> starts the lab’s models, {served.titles}, on your
              machine, where your code can call each by its name at{' '}
              <code>http://127.0.0.1:9931/v1</code>. The first time, it downloads the models,{' '}
              {served.size}, from {served.hosts}, and llama.cpp’s server for your system, from
              github.com.
            </p>
          )}
          {typeScript && (
            <p>
              Its TypeScript stages run in Node.js. The first time, it downloads Node.js for your
              system from nodejs.org, and the lab’s packages from registry.npmjs.org.
            </p>
          )}
          {go && (
            <p>
              Its Go stages run with Go. The first time, it downloads Go for your system from
              dl.google.com.
            </p>
          )}
          {java && (
            <p>
              Its Java stages run with Java. The first time, it downloads a JDK for your system from
              github.com, and JUnit and Jackson from repo1.maven.org.
            </p>
          )}
          {isCatch && (
            <p>
              Fix every problem you find in <code>{stage.file}</code>, then finish the review with{' '}
              <code>uv run sulba.py finish</code>.
            </p>
          )}
          <p>A download starts at the first stage you haven’t done.</p>
        </div>
        <div className={css.dock}>
          {isCatch && review && (
            <div className={`${css.done} ${css.reviewed}`}>
              <p>
                Review finished. You caught {review.caught.length} of {review.total} problems.
              </p>
              <div className={css.tools}>
                <Button variant="outline" size="small" onPress={() => setTab('explanation')}>
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
          {!isCatch && passed && (
            <div className={css.done}>
              <p>Stage {index + 1} done.</p>
              {onNext && (
                <div className={css.tools}>
                  <Button size="small" onPress={onNext}>
                    Next stage
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

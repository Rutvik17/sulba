import type { Event } from '@sulba/data/outbox';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Segment, SegmentedChoice } from '@sulba/ui/segmented';
import { Tab, TabList, TabPanel, Tabs } from '@sulba/ui/tabs';
import { type Ref, useEffect, useId, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import type { LabView, StageView } from '../lib/labs';
import { answeredIn, type DesignState, designElapsed, metOf, startDesign } from './design';
import { useNow } from './now';
import { clock } from './problem';
import { passOf } from './progress';
import { Line } from './Results';
import { Hints, Prose } from './StageParts';
import { type Stopwatch, stopwatch } from './stopwatch';
import { kept } from './storage';
import styles from './workspace.module.css';

const css = classes(
  styles,
  'workspace',
  'left',
  'panel',
  'builds',
  'right',
  'sheet',
  'head',
  'file',
  'tools',
  'design',
  'write',
  'rubric',
  'point',
  'caught',
  'missed',
  'done',
  'reviewed',
  'note',
  'clock',
  'over',
  'start',
);

interface DesignProps {
  readonly lab: LabView;
  readonly index: number;
  readonly passed: boolean;
  readonly onPass: () => void;
  readonly onNext: (() => void) | null;
  /** Keeps what the learner did, with the seconds since their last attempt in this stage. */
  readonly record: (event: Event, seconds: number) => void;
}

/**
 * A Design stage (decision record 42): the learner writes a design against the clock, answers the
 * follow-up questions, then marks their design against the rubric. It passes when they meet enough
 * of its points, and a design that doesn't starts again.
 */
export default function DesignWorkspace({
  lab,
  index,
  passed,
  onPass,
  onNext,
  record,
}: DesignProps) {
  const stage = lab.stages[index] as StageView;
  const [state, setState] = useState<DesignState | null>(() => kept.design(stage.id));
  const keep = (next: DesignState) => {
    setState(next);
    kept.saveDesign(stage.id, next);
  };
  // The clock runs until the answers are in. A design passed on another device kept no attempt
  // here, so it shows no clock.
  const now = useNow(state !== null && state.answered === null && !passed);
  const seconds = state ? designElapsed(state, now) : 0;
  const timed = state !== null && (state.answered !== null || !passed);
  const started = passed || state !== null;
  // The explanation is the model design, which opens with the rubric and stays open after it.
  const explained = passed || (state !== null && (state.answered !== null || state.attempts > 1));
  const met = state ? metOf(state) : 0;
  const settled = state?.marked === true;
  const [tab, setTab] = useState('brief');
  const [hints, setHints] = useState(0);
  const id = useId();
  const left = useRef<HTMLDivElement>(null);
  const brief = useRef<HTMLDivElement>(null);
  const designBox = useRef<HTMLTextAreaElement>(null);
  const firstAnswer = useRef<HTMLTextAreaElement>(null);
  const rubric = useRef<HTMLHeadingElement>(null);
  const result = useRef<HTMLParagraphElement>(null);
  const watch = useRef<Stopwatch | null>(null);

  useEffect(() => {
    const each = stopwatch();
    watch.current = each;
    return () => each.stop();
  }, []);

  const lap = () => watch.current?.lap() ?? 0;

  const show = (panel: string) => {
    setTab(panel);
    left.current?.scrollIntoView({ block: 'nearest' });
  };

  // Each step moves the focus to what it opens: the brief, the first question, the rubric, the
  // result, or the design again.
  const start = () => {
    flushSync(() => keep(startDesign(Date.now(), state)));
    brief.current?.focus();
  };
  const handIn = (current: DesignState) => {
    flushSync(() => keep({ ...current, handedIn: true, answers: stage.questions.map(() => '') }));
    firstAnswer.current?.focus();
  };
  const handInAnswers = (current: DesignState) => {
    const answered = designElapsed(current, Date.now());
    flushSync(() => keep({ ...current, answered, marks: stage.rubric.map(() => false) }));
    rubric.current?.focus();
  };
  const finish = (current: DesignState) => {
    const done = { ...current, marked: true };
    flushSync(() => keep(done));
    result.current?.focus();
    if (metOf(done) >= stage.pass && !passed) {
      record(passOf(stage, null), lap());
      onPass();
    }
  };
  const again = (current: DesignState) => {
    flushSync(() => keep(startDesign(Date.now(), current)));
    designBox.current?.focus();
  };

  return (
    <section className={css.workspace} aria-label={`Stage ${index + 1}: ${stage.title}`}>
      <div className={css.left} ref={left}>
        <Tabs selectedKey={tab} onSelectionChange={(key) => setTab(String(key))}>
          <TabList aria-label="Stage">
            <Tab id="brief">Brief</Tab>
            {stage.hints.length > 0 && started && <Tab id="hints">Hints</Tab>}
            <Tab id="explanation">Explanation</Tab>
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
                    You have {stage.minutes} minutes from when you start. Write your design, then
                    answer the follow-up questions. Then mark your design against the rubric.
                  </p>
                  <Button onPress={start}>Start</Button>
                </div>
              )}
            </div>
          </TabPanel>
          {stage.hints.length > 0 && started && (
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
              {explained ? (
                <Prose html={stage.explanation} />
              ) : (
                <p className={css.note}>Opens when you hand in your answers.</p>
              )}
            </div>
          </TabPanel>
        </Tabs>
      </div>

      <div className={`${css.right} ${css.sheet}`}>
        <div className={css.head}>
          <span className={css.file}>
            {state && state.attempts > 1 ? `Attempt ${state.attempts}` : 'Design'}
          </span>
          {timed && (
            <span
              role="timer"
              className={seconds > stage.minutes * 60 ? `${css.clock} ${css.over}` : css.clock}
            >
              {clock(seconds, stage.minutes)}
            </span>
          )}
        </div>
        <div className={css.design}>
          {state === null ? (
            passed ? (
              <>
                <p className={css.done}>Stage {index + 1} done.</p>
                <Rubric stage={stage} />
              </>
            ) : (
              <p className={css.note}>
                Your design, then your answers to the follow-up questions, go here once you start.
              </p>
            )
          ) : (
            <>
              <form
                className={css.write}
                onSubmit={(event) => {
                  event.preventDefault();
                  handIn(state);
                }}
              >
                <label htmlFor={`${id}-design`}>Your design</label>
                <p id={`${id}-about`} className={css.note}>
                  What it must do and at what scale, its parts and how they fit, and the trade-offs
                  you chose.
                </p>
                <textarea
                  ref={designBox}
                  id={`${id}-design`}
                  aria-describedby={`${id}-about`}
                  value={state.design}
                  readOnly={state.handedIn}
                  onChange={(event) => keep({ ...state, design: event.target.value })}
                />
                {!state.handedIn && (
                  <div>
                    <Button type="submit" isDisabled={state.design.trim() === ''}>
                      Hand in the design
                    </Button>
                  </div>
                )}
              </form>
              {state.handedIn && (
                <form
                  className={css.write}
                  aria-labelledby={`${id}-questions`}
                  onSubmit={(event) => {
                    event.preventDefault();
                    handInAnswers(state);
                  }}
                >
                  <h3 id={`${id}-questions`}>Follow-up questions</h3>
                  {stage.questions.map((question, at) => (
                    <div key={question} className={css.write}>
                      <label htmlFor={`${id}-answer-${at}`}>
                        <Line html={question} />
                      </label>
                      <textarea
                        ref={at === 0 ? firstAnswer : undefined}
                        id={`${id}-answer-${at}`}
                        value={state.answers[at] ?? ''}
                        readOnly={state.answered !== null}
                        onChange={(event) =>
                          keep({
                            ...state,
                            answers: state.answers.map((answer, each) =>
                              each === at ? event.target.value : answer,
                            ),
                          })
                        }
                      />
                    </div>
                  ))}
                  {state.answered === null && (
                    <div>
                      <Button
                        type="submit"
                        isDisabled={
                          state.answers.length !== stage.questions.length ||
                          state.answers.some((answer) => answer.trim() === '')
                        }
                      >
                        Hand in the answers
                      </Button>
                    </div>
                  )}
                </form>
              )}
              {state.answered !== null && (
                <>
                  <Rubric
                    stage={stage}
                    heading={rubric}
                    handedIn={answeredIn(state.answered, stage.minutes)}
                    marks={state.marks}
                    onMark={
                      settled
                        ? null
                        : (at, mark) =>
                            keep({
                              ...state,
                              marks: state.marks.map((each, point) => (point === at ? mark : each)),
                            })
                    }
                  />
                  {!settled && (
                    <div>
                      <Button onPress={() => finish(state)}>Finish marking</Button>
                    </div>
                  )}
                </>
              )}
              {settled && (
                <div className={met >= stage.pass ? css.done : `${css.done} ${css.reviewed}`}>
                  <p ref={result} tabIndex={-1}>
                    {met >= stage.pass
                      ? `Stage ${index + 1} done. You met ${met} of ${stage.rubric.length} points, and it needs ${stage.pass}.`
                      : `You met ${met} of ${stage.rubric.length} points, and the stage needs ${stage.pass}.`}
                  </p>
                  <div className={css.tools}>
                    {met < stage.pass && (
                      <>
                        <Button variant="outline" size="small" onPress={() => show('explanation')}>
                          Read the explanation
                        </Button>
                        <Button size="small" onPress={() => again(state)}>
                          Start again
                        </Button>
                      </>
                    )}
                    {met >= stage.pass && onNext && (
                      <Button size="small" onPress={onNext}>
                        Next stage
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}

/**
 * A Design stage's rubric: each point, with what a strong design says to it, and the learner's
 * mark: a choice of Met or Not met while `onMark` takes one, then the mark they gave. Without
 * marks, it shows the points alone.
 */
function Rubric({
  stage,
  heading,
  handedIn,
  marks,
  onMark,
}: {
  stage: StageView;
  heading?: Ref<HTMLHeadingElement>;
  /** When the answers came in, against the stage's minutes. */
  handedIn?: string;
  marks?: readonly boolean[];
  onMark?: ((at: number, mark: boolean) => void) | null;
}) {
  const id = useId();
  return (
    <section className={css.write} aria-labelledby={`${id}-rubric`}>
      <h3 id={`${id}-rubric`} ref={heading} tabIndex={-1}>
        Rubric
      </h3>
      {handedIn && <p className={css.note}>{handedIn}</p>}
      <p className={css.note}>
        {marks
          ? `Mark each point your design and answers meet. The stage needs ${stage.pass} of its ${stage.rubric.length} points.`
          : `The stage needs ${stage.pass} of its ${stage.rubric.length} points.`}
      </p>
      <ol className={css.rubric}>
        {stage.rubric.map(({ point, answer }, at) => {
          const met = marks?.[at] === true;
          return (
            <li key={point}>
              <p id={`${id}-point-${at}`} className={css.point}>
                <Line html={point} />
              </p>
              <p>
                <Line html={answer} />
              </p>
              {marks && onMark && (
                <SegmentedChoice
                  aria-labelledby={`${id}-point-${at}`}
                  value={met ? 'met' : 'not'}
                  onChange={(value) => onMark(at, value === 'met')}
                >
                  <Segment value="met">Met</Segment>
                  <Segment value="not">Not met</Segment>
                </SegmentedChoice>
              )}
              {marks && !onMark && (
                <p className={met ? css.caught : css.missed}>{met ? 'Met' : 'Not met'}</p>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}

import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { useEffect, useRef } from 'react';
import type { LabView, ProblemView, StageView } from '../lib/labs';
import { keyboardScrollBoxes } from '../lib/scroll-boxes';
import { isOpen, type Review } from './stages';
import { kept } from './storage';
import styles from './workspace.module.css';

// The parts of a stage both workspaces show: in this page, and for a lab that runs on the learner's
// machine.
const css = classes(
  styles,
  'stages',
  'stage',
  'number',
  'kind',
  'state',
  'prose',
  'hints',
  'problems',
  'caught',
  'missed',
);

const kinds: Record<StageView['kind'], string> = {
  build: 'Build',
  catch: 'Catch',
  ship: 'Ship',
  problem: 'Problem',
  design: 'Design',
};

/** A lab's stages, each with its kind and state, opening the one the learner picks. */
export function StageNav({
  lab,
  index,
  passed,
  reviews,
  onOpen,
}: {
  lab: LabView;
  index: number;
  passed: readonly StageView[];
  reviews: Readonly<Record<string, Review>>;
  onOpen: (index: number) => void;
}) {
  const stateOf = (each: StageView, at: number) => {
    const review = reviews[each.id];
    if (review) return `${review.caught.length} of ${review.total} caught`;
    if (passed.some((done) => done.id === each.id)) return 'Done';
    return isOpen(lab, at, kept) ? '' : `Opens when stage ${at} is done`;
  };
  return (
    <nav aria-label="Stages">
      <ol className={css.stages}>
        {lab.stages.map((each, at) => (
          <li key={each.id}>
            <button
              type="button"
              className={css.stage}
              aria-current={at === index ? 'step' : undefined}
              disabled={!isOpen(lab, at, kept)}
              onClick={() => onOpen(at)}
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
  );
}

/** Prose made from a course's Markdoc files when the site was built. */
export function Prose({ html }: { html: string }) {
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

/** A stage's hints, the first `shown` of them, and a button that shows the next. */
export function Hints({
  hints,
  shown,
  onShow,
}: {
  hints: readonly string[];
  shown: number;
  onShow: () => void;
}) {
  return (
    <>
      {shown > 0 && (
        <ol className={css.hints}>
          {hints.slice(0, shown).map((hint) => (
            <li key={hint}>
              <Prose html={hint} />
            </li>
          ))}
        </ol>
      )}
      {shown < hints.length ? (
        <Button variant="outline" size="small" onPress={onShow}>
          {shown === 0 ? 'Show a hint' : 'Show the next hint'}
        </Button>
      ) : (
        <p>No more hints.</p>
      )}
    </>
  );
}

/** A finished review's problems: each one caught or missed, what it would cost, and its fix. */
export function Problems({
  problems,
  review,
}: {
  problems: readonly ProblemView[];
  review: Review;
}) {
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

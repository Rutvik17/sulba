// Where a learner is in a lab, from what this browser keeps: the stage to open, the Catch reviews
// they finished, and the stages passed in their account, taken in on another device's behalf.
import type { Event } from '@sulba/data/outbox';
import type { Passed } from '@sulba/data/sync';
import type { LabView, StageView } from '../lib/labs';
import { isOpen, type Review } from './stages';
import { kept } from './storage';

/** The stage to open: the one the address names if it's open, else the first not yet passed. */
export function firstStage(lab: LabView): number {
  const named = new URLSearchParams(location.search).get('stage');
  const index = lab.stages.findIndex((stage) => stage.slug === named);
  if (index >= 0 && isOpen(lab, index, kept)) return index;
  const next = lab.stages.findIndex((stage) => !kept.passed(stage.id));
  return next >= 0 ? next : lab.stages.length - 1;
}

/** Each finished Catch review this browser kept, by stage id. */
export function reviewsOf(lab: LabView): Record<string, Review> {
  const found: Record<string, Review> = {};
  for (const stage of lab.stages) {
    const review = stage.kind === 'catch' ? kept.review(stage.id) : null;
    if (review) found[stage.id] = review;
  }
  return found;
}

/** Keeps in this browser the stages passed elsewhere, with their reviews. */
export function takeIn(lab: LabView, passed: readonly Passed[]) {
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
export function passOf(stage: StageView, review: Review | null): Event {
  return {
    kind: 'pass',
    review:
      stage.kind === 'catch' && review ? { caught: review.caught, problems: review.total } : null,
  };
}

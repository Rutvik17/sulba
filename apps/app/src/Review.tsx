import {
  answerProblem,
  type Review,
  removeReviewer,
  requestReview,
  reviewerLimit,
  reviewSpec,
  type Verdict,
  verdictNames,
} from '@sulba/data/reviewers';
import { type Spec, specKey } from '@sulba/data/specs';
import type { Member } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { Menu, MenuItem, MenuTrigger } from '@sulba/ui/menu';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useAccount } from './account';
import { useCommands } from './commands';
import { Notice } from './Notice';
import { keys } from './queries';
import { useWorkspace } from './Shell';
import styles from './spec.module.css';

const css = classes(
  styles,
  'reviewers',
  'reviewer',
  'verdict',
  'said',
  'tools',
  'banner',
  'actions',
  'note',
);

const nameOf = (member: Member | undefined) => member?.name || member?.email || 'Someone';

/** Reads again what a review changes: the spec, its reviews, its history and My work. */
function useReread(spec: Spec) {
  const workspace = useWorkspace();
  const queryClient = useQueryClient();
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: keys.reviews(spec.id) }),
      queryClient.invalidateQueries({ queryKey: keys.spec(workspace.id, spec.number) }),
      queryClient.invalidateQueries({ queryKey: keys.specs(workspace.id) }),
      queryClient.invalidateQueries({ queryKey: keys.history(spec.id) }),
      queryClient.invalidateQueries({ queryKey: keys.work(workspace.id) }),
    ]);
}

/**
 * The spec's reviewers and what each answered, in its details (decision record 52). Members add
 * reviewers from the workspace's people while the spec is a draft or in review, take them off and
 * ask them again.
 */
export function Reviewers({
  spec,
  reviews,
  members,
  canWrite,
}: {
  spec: Spec;
  reviews: readonly Review[];
  members: readonly Member[];
  canWrite: boolean;
}) {
  const { client } = useAccount();
  const reread = useReread(spec);
  const [failure, setFailure] = useState<string | null>(null);
  const byId = new Map(members.map((member) => [member.personId, member]));
  const choosing = canWrite && (spec.status === 'draft' || spec.status === 'in_review');
  const eligible = members.filter(
    (member) =>
      member.personId !== spec.ownerId &&
      !reviews.some((review) => review.reviewerId === member.personId),
  );

  const ask = useMutation({
    mutationFn: (reviewerId: string) => requestReview(client, spec.id, reviewerId),
    onMutate: () => setFailure(null),
    onSuccess: reread,
    onError: (error) => setFailure(error.message),
  });
  const remove = useMutation({
    mutationFn: (reviewerId: string) => removeReviewer(client, spec.id, reviewerId),
    onMutate: () => setFailure(null),
    onSuccess: reread,
    onError: (error) => setFailure(error.message),
  });
  const adding = choosing && eligible.length > 0 && reviews.length < reviewerLimit;
  useCommands(
    adding
      ? [
          {
            id: 'spec-reviewer',
            label: 'Add a reviewer',
            group: specKey(spec.number),
            keys: ['r'],
            does: {
              title: 'Add a reviewer',
              actions: eligible.map((member) => ({
                id: member.personId,
                label: nameOf(member),
                run: () => ask.mutate(member.personId),
              })),
            },
          },
        ]
      : [],
  );

  return (
    <>
      {reviews.length ? (
        <ul className={css.reviewers}>
          {reviews.map((review) => {
            const name = nameOf(byId.get(review.reviewerId));
            return (
              <li key={review.id} className={css.reviewer}>
                <span>{name}</span>
                <span className={css.verdict} data-verdict={review.verdict}>
                  {verdictNames[review.verdict]}
                </span>
                {review.note ? <q className={css.said}>{review.note}</q> : null}
                {choosing ? (
                  <span className={css.tools}>
                    {review.verdict === 'pending' ? null : (
                      <Button
                        variant="ghost"
                        size="small"
                        aria-label={`Ask ${name} again`}
                        onPress={() => ask.mutate(review.reviewerId)}
                        isDisabled={ask.isPending}
                      >
                        Ask again
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="small"
                      aria-label={`Remove ${name}`}
                      onPress={() => remove.mutate(review.reviewerId)}
                      isDisabled={remove.isPending}
                    >
                      Remove
                    </Button>
                  </span>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : (
        <span className={css.note}>None</span>
      )}
      {adding ? (
        <MenuTrigger>
          <Button variant="outline" size="small" isDisabled={ask.isPending}>
            Add reviewer
          </Button>
          <Menu
            aria-label="People who can review it"
            items={eligible}
            onAction={(id) => ask.mutate(String(id))}
          >
            {(member) => (
              <MenuItem id={member.personId} textValue={nameOf(member)}>
                {nameOf(member)}
              </MenuItem>
            )}
          </Menu>
        </MenuTrigger>
      ) : null}
      <Notice text={failure} />
    </>
  );
}

const asked: Record<Verdict, (by: string) => string> = {
  pending: (by) => `${by} asked you to review this spec.`,
  approved: () => 'You approved this spec. It’s approved once every reviewer has.',
  changes_requested: () =>
    'You asked for changes. Approve it once they’re made, or say what else should change.',
};

/** What the signed-in person, as one of the spec's reviewers, can answer while it's in review. */
export function YourReview({
  spec,
  review,
  members,
}: {
  spec: Spec;
  review: Review;
  members: readonly Member[];
}) {
  const { client } = useAccount();
  const reread = useReread(spec);
  const [asking, setAsking] = useState(false);
  const [note, setNote] = useState('');
  const by = nameOf(members.find((member) => member.personId === review.requestedBy));

  const answer = useMutation({
    mutationFn: (verdict: Exclude<Verdict, 'pending'>) =>
      reviewSpec(client, spec.id, verdict, verdict === 'approved' ? '' : note),
    onSuccess: async () => {
      setAsking(false);
      setNote('');
      await reread();
    },
  });
  const problem = answerProblem('changes_requested', note);
  const key = specKey(spec.number);
  useCommands([
    ...(review.verdict === 'approved'
      ? []
      : [
          {
            id: 'spec-approve',
            label: `Approve ${key}`,
            group: key,
            does: () => answer.mutate('approved'),
          },
        ]),
    {
      id: 'spec-changes',
      label: `Request changes to ${key}`,
      group: key,
      does: () => setAsking(true),
    },
  ]);

  return (
    <section className={css.banner} aria-label="Your review">
      <p>{asked[review.verdict](by)}</p>
      <div className={css.actions}>
        {review.verdict === 'approved' ? null : (
          <Button
            size="small"
            onPress={() => answer.mutate('approved')}
            isDisabled={answer.isPending}
          >
            Approve
          </Button>
        )}
        <Button size="small" variant="outline" onPress={() => setAsking(true)}>
          Request changes
        </Button>
      </div>
      {asking ? null : <Notice text={answer.error?.message ?? null} />}
      <Dialog
        title={`Request changes to ${key}`}
        isOpen={asking}
        onOpenChange={(open) => {
          setAsking(open);
          if (!open) answer.reset();
        }}
        actions={
          <>
            <Button slot="close" variant="outline">
              Cancel
            </Button>
            <Button
              onPress={() => answer.mutate('changes_requested')}
              isDisabled={problem !== null || answer.isPending}
            >
              Request changes
            </Button>
          </>
        }
      >
        <TextField
          label="What should change?"
          multiline
          value={note}
          onChange={setNote}
          description="The spec’s owner sees your note beside your review."
          autoFocus
        />
        <Notice text={answer.error?.message ?? null} />
      </Dialog>
    </section>
  );
}

import {
  approveRelease,
  type Release,
  releaseBlockers,
  releaseDocument,
} from '@sulba/data/releases';
import { type Request, requestKey } from '@sulba/data/requests';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { type FormEvent, useState } from 'react';
import { useAccount } from './account';
import { Notice } from './Notice';
import pageStyles from './page.module.css';
import { keys, useProofs, useReleases } from './queries';
import ownStyles from './request.module.css';
import { useWorkspace } from './Shell';
import styles from './spec.module.css';
import { When } from './When';

const css = classes(styles, 'section', 'heading', 'note', 'key');
const own = classes(ownStyles, 'drafted', 'blockers', 'release', 'made', 'by', 'said');
const page = classes(pageStyles, 'form');

/**
 * A request's delivery (decision record 62): what still stands between it and a release, the
 * button a member approves one with once every spec drafted from it is approved and every criterion
 * proven, and each release with its document to download.
 */
export function Delivery({
  request,
  canWrite,
  names,
}: {
  request: Request;
  canWrite: boolean;
  names: ReadonlyMap<string, string | null>;
}) {
  const workspace = useWorkspace();
  const { data: proofs } = useProofs(workspace);
  const { data: releases } = useReleases(request.id);
  const [approving, setApproving] = useState(false);
  const blockers = releaseBlockers(request.specs, proofs);
  const approverOf = (release: Release) =>
    (release.approvedBy && names.get(release.approvedBy)) || 'someone who has left';

  const download = (release: Release) => {
    const text = releaseDocument(request, release, approverOf(release));
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([text], { type: 'text/markdown' }));
    link.download = `${requestKey(request.number)}-release-${release.number}.md`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  return (
    <section className={css.section} aria-labelledby="delivery">
      <h2 id="delivery" className={css.heading}>
        Delivery
      </h2>
      {request.status === 'closed' ? (
        <p className={css.note}>This request is closed, so it has nothing to release.</p>
      ) : blockers.length ? (
        <>
          <p className={css.note}>
            Release {releases.length + 1} can be approved once these are done:
          </p>
          <ul className={own.blockers}>
            {blockers.map((blocker) => (
              <li key={blocker}>{blocker}</li>
            ))}
          </ul>
        </>
      ) : (
        <p className={css.note}>
          Every spec drafted from it is approved and every criterion is proven by the tests.
        </p>
      )}
      {canWrite && request.status !== 'closed' ? (
        <div>
          <Button size="small" isDisabled={blockers.length > 0} onPress={() => setApproving(true)}>
            Approve release {releases.length + 1}
          </Button>
        </div>
      ) : null}
      {releases.length ? (
        <ul className={own.drafted}>
          {releases.map((release) => (
            <li key={release.id} className={own.release}>
              <span className={css.key}>Release {release.number}</span>
              <div className={own.made}>
                <span className={own.by}>
                  Approved by {approverOf(release)} · <When at={release.approvedAt} day />
                </span>
                {release.note ? <span className={own.said}>{release.note}</span> : null}
              </div>
              <Button variant="outline" size="small" onPress={() => download(release)}>
                Download
              </Button>
            </li>
          ))}
        </ul>
      ) : null}
      <Approve
        request={request}
        number={releases.length + 1}
        isOpen={approving}
        onClose={() => setApproving(false)}
      />
    </section>
  );
}

/** Asks for an optional note, then approves the next release. */
function Approve({
  request,
  number,
  isOpen,
  onClose,
}: {
  request: Request;
  number: number;
  isOpen: boolean;
  onClose: () => void;
}) {
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const [note, setNote] = useState('');
  const close = () => {
    onClose();
    setNote('');
    approve.reset();
  };
  const approve = useMutation({
    mutationFn: () => approveRelease(client, request.id, note),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: keys.releases(request.id) });
      close();
    },
  });
  const submit = (event: FormEvent) => {
    event.preventDefault();
    approve.mutate();
  };

  return (
    <Dialog
      title={`Approve release ${number} of ${requestKey(request.number)}`}
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) close();
      }}
      actions={
        <>
          <Button slot="close" variant="outline">
            Cancel
          </Button>
          <Button type="submit" form="approve-release" isDisabled={approve.isPending}>
            {approve.isPending ? 'Approving…' : 'Approve release'}
          </Button>
        </>
      }
    >
      <form id="approve-release" className={page.form} onSubmit={submit} noValidate>
        <p>
          The release keeps each spec drafted from the request as it is now, with the tests that
          prove each criterion, and its document says you approved it.
        </p>
        <TextField
          label="Note"
          value={note}
          onChange={setNote}
          multiline
          description="Optional. What this release is for, such as who it goes to."
        />
        <Notice text={approve.error?.message ?? null} />
      </form>
    </Dialog>
  );
}

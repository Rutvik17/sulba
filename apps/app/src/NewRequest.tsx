import { createRequest, requestKey, requestTitleProblem } from '@sulba/data/requests';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { type FormEvent, useState } from 'react';
import { useAccount } from './account';
import { Notice } from './Notice';
import styles from './page.module.css';
import { keys } from './queries';
import { useWorkspace } from './Shell';

const css = classes(styles, 'form');

/** Writes a request in its writer's own words, then opens it. */
export function NewRequest({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [checked, setChecked] = useState(false);

  const create = useMutation({
    mutationFn: () => createRequest(client, workspace.id, title, body),
    onSuccess: async (number) => {
      await queryClient.invalidateQueries({ queryKey: keys.requests(workspace.id) });
      close();
      await navigate({
        to: '/$slug/$spec',
        params: { slug: workspace.slug, spec: requestKey(number) },
      });
    },
  });

  const close = () => {
    onClose();
    setTitle('');
    setBody('');
    setChecked(false);
    create.reset();
  };
  const titleError = checked ? requestTitleProblem(title) : null;
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setChecked(true);
    if (requestTitleProblem(title)) return;
    create.mutate();
  };

  return (
    <Dialog
      title="New request"
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) close();
      }}
      actions={
        <>
          <Button slot="close" variant="outline">
            Cancel
          </Button>
          <Button type="submit" form="new-request" isDisabled={create.isPending}>
            {create.isPending ? 'Sending…' : 'Send request'}
          </Button>
        </>
      }
    >
      <form id="new-request" className={css.form} onSubmit={submit} noValidate>
        <TextField
          label="What do you want built?"
          value={title}
          onChange={setTitle}
          error={titleError}
          placeholder="A booking app for our gym"
          autoFocus
        />
        <TextField
          label="Details"
          value={body}
          onChange={setBody}
          multiline
          description="Who it’s for, what they should be able to do, and anything it must work with. An agent asks about the rest."
          placeholder="Members book and pay for classes from their phones. It works with our card reader."
        />
        <Notice text={create.error?.message ?? null} />
      </form>
    </Dialog>
  );
}

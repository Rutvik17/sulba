import { createSpec, criterionProblem, specKey, titleProblem } from '@sulba/data/specs';
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

/** Writes a spec with its title and first acceptance criterion, then opens it. */
export function NewSpec({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [criterion, setCriterion] = useState('');
  const [checked, setChecked] = useState(false);

  const create = useMutation({
    mutationFn: () => createSpec(client, workspace.id, title, [criterion]),
    onSuccess: async (number) => {
      await queryClient.invalidateQueries({ queryKey: keys.specs(workspace.id) });
      close();
      await navigate({
        to: '/$slug/$spec',
        params: { slug: workspace.slug, spec: specKey(number) },
      });
    },
  });

  const close = () => {
    onClose();
    setTitle('');
    setCriterion('');
    setChecked(false);
    create.reset();
  };
  const titleError = checked ? titleProblem(title) : null;
  const criterionError = checked ? criterionProblem(criterion) : null;
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setChecked(true);
    if (titleProblem(title) || criterionProblem(criterion)) return;
    create.mutate();
  };

  return (
    <Dialog
      title="New spec"
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) close();
      }}
      actions={
        <>
          <Button slot="close" variant="outline">
            Cancel
          </Button>
          <Button type="submit" form="new-spec" isDisabled={create.isPending}>
            {create.isPending ? 'Creating…' : 'Create spec'}
          </Button>
        </>
      }
    >
      <form id="new-spec" className={css.form} onSubmit={submit} noValidate>
        <TextField
          label="Title"
          value={title}
          onChange={setTitle}
          error={titleError}
          placeholder="Retry failed payments"
          autoFocus
        />
        <TextField
          label="First acceptance criterion"
          value={criterion}
          onChange={setCriterion}
          error={criterionError}
          description="One statement a test can check. You can add more on the spec’s page."
          placeholder="When a payment fails, the system shall retry it once after 30 seconds"
        />
        <Notice text={create.error?.message ?? null} />
      </form>
    </Dialog>
  );
}

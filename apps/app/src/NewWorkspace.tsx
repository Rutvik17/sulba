import { createWorkspace, nameProblem, Refusal, slugOf, slugProblem } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { type FormEvent, useState } from 'react';
import { useAccount } from './account';
import { Centered, centeredForm } from './Centered';
import { Notice } from './Notice';
import { keys } from './queries';

const taken = 'That address is taken.';

/**
 * Creates a workspace. Its address follows the name until the person edits it, and each field
 * says what's wrong with it once they've left it or tried to create the workspace.
 */
export function NewWorkspace() {
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [typedSlug, setTypedSlug] = useState<string | null>(null);
  const [checked, setChecked] = useState({ name: false, slug: false });
  const [takenSlug, setTakenSlug] = useState<string | null>(null);

  const slug = typedSlug ?? slugOf(name);
  const create = useMutation({
    mutationFn: () => createWorkspace(client, name.trim(), slug),
    onSuccess: async (made) => {
      await queryClient.invalidateQueries({ queryKey: keys.workspaces });
      await navigate({ to: '/$slug', params: { slug: made } });
    },
    onError: (error) => {
      if (error instanceof Refusal && error.message === taken) setTakenSlug(slug);
    },
  });

  const nameError = checked.name ? nameProblem(name) : null;
  const slugError =
    takenSlug === slug ? taken : checked.slug || typedSlug !== null ? slugProblem(slug) : null;
  const failure =
    create.error && !(create.error instanceof Refusal && create.error.message === taken)
      ? create.error.message
      : null;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setChecked({ name: true, slug: true });
    if (nameProblem(name) || slugProblem(slug) || takenSlug === slug) return;
    create.mutate();
  };

  return (
    <Centered
      title="Create a workspace"
      lead="A workspace is where your team works in Sulba. You can rename it later."
    >
      <form onSubmit={submit} noValidate className={centeredForm}>
        <TextField
          label="Workspace name"
          value={name}
          onChange={setName}
          onBlur={() => setChecked((was) => ({ ...was, name: true }))}
          error={nameError}
          autoFocus
          autoComplete="organization"
        />
        <TextField
          label="Address"
          prefix="sulba.dev/app/"
          value={slug}
          onChange={(value) => setTypedSlug(value.toLowerCase())}
          onBlur={() => setChecked((was) => ({ ...was, slug: true }))}
          error={slugError}
          description={`The workspace will be at sulba.dev/app/${slug || '…'}. Its address can’t be changed.`}
          autoComplete="off"
          spellCheck="false"
        />
        <Notice text={failure} />
        <Button type="submit" isDisabled={create.isPending}>
          {create.isPending ? 'Creating…' : 'Create workspace'}
        </Button>
      </form>
    </Centered>
  );
}

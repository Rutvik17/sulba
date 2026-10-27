import {
  deleteWorkspace,
  holds,
  nameProblem,
  removeMember,
  renameWorkspace,
  roleNames,
} from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { type FormEvent, useState } from 'react';
import { useAccount } from './account';
import { forgetWorkspace } from './last';
import { Notice } from './Notice';
import styles from './page.module.css';
import { keys } from './queries';
import { useWorkspace } from './Shell';
import { useTitle } from './title';

const css = classes(
  styles,
  'page',
  'header',
  'title',
  'count',
  'section',
  'heading',
  'note',
  'card',
  'danger',
);

/**
 * The workspace's name and address, and leaving or deleting it. Admins rename it; only an owner
 * deletes it, after typing its name.
 */
export function Settings() {
  const workspace = useWorkspace();
  useTitle('Settings', workspace.name);
  const { client, personId } = useAccount();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const isAdmin = holds(workspace.role, 'admin');
  const isOwner = workspace.role === 'owner';
  const [name, setName] = useState(workspace.name);
  const [checked, setChecked] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const gone = async () => {
    forgetWorkspace(workspace.slug);
    queryClient.removeQueries({ queryKey: keys.workspace(workspace.slug) });
    await queryClient.invalidateQueries({ queryKey: keys.workspaces });
    await navigate({ to: '/' });
  };

  const rename = useMutation({
    mutationFn: () => renameWorkspace(client, workspace.id, name),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: keys.workspace(workspace.slug) }),
        queryClient.invalidateQueries({ queryKey: keys.workspaces }),
      ]),
  });
  const leave = useMutation({
    mutationFn: () => removeMember(client, workspace.id, personId),
    onSuccess: gone,
    onSettled: () => setLeaving(false),
  });

  const nameError = checked ? nameProblem(name) : null;
  const unchanged = name.trim() === workspace.name;
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setChecked(true);
    if (nameProblem(name) || unchanged) return;
    rename.mutate();
  };

  return (
    <div className={css.page}>
      <header className={css.header}>
        <div>
          <h1 className={css.title}>Settings</h1>
          <p className={css.count}>You’re {article(roleNames[workspace.role])} here.</p>
        </div>
      </header>

      <section className={css.section} aria-labelledby="workspace">
        <h2 id="workspace" className={css.heading}>
          Workspace
        </h2>
        <form className={css.card} onSubmit={submit} noValidate>
          <TextField
            label="Name"
            value={name}
            onChange={(value) => {
              setName(value);
              rename.reset();
            }}
            onBlur={() => setChecked(true)}
            error={nameError}
            isReadOnly={!isAdmin}
            {...(isAdmin ? {} : { description: 'Only admins and owners can rename it.' })}
          />
          <TextField
            label="Address"
            value={`sulba.dev/app/${workspace.slug}`}
            isReadOnly
            description="A workspace’s address can’t be changed."
          />
          <Notice text={rename.error?.message ?? null} />
          {isAdmin ? (
            <Button type="submit" isDisabled={unchanged || rename.isPending}>
              {rename.isSuccess && unchanged ? 'Saved' : 'Save'}
            </Button>
          ) : null}
        </form>
      </section>

      <section className={css.section} aria-labelledby="leave">
        <h2 id="leave" className={css.heading}>
          Leave
        </h2>
        <div className={css.card}>
          <p className={css.note}>
            You lose access to {workspace.name} at once, and need a new invitation to come back.
            {isOwner ? ' If you’re its only owner, make someone else an owner first.' : ''}
          </p>
          <Notice text={leave.error?.message ?? null} />
          <Button variant="outline" onPress={() => setLeaving(true)}>
            Leave workspace
          </Button>
        </div>
      </section>

      {isOwner ? (
        <section className={css.section} aria-labelledby="delete">
          <h2 id="delete" className={css.heading}>
            Delete
          </h2>
          <div className={`${css.card} ${css.danger}`}>
            <p className={css.note}>
              Deleting {workspace.name} removes it and everything in it for every member. It can’t
              be undone.
            </p>
            <Button variant="outline" onPress={() => setDeleting(true)}>
              Delete workspace
            </Button>
          </div>
        </section>
      ) : null}

      <Dialog
        title={`Leave ${workspace.name}?`}
        isOpen={leaving}
        onOpenChange={setLeaving}
        actions={
          <>
            <Button slot="close" variant="outline">
              Cancel
            </Button>
            <Button onPress={() => leave.mutate()} isDisabled={leave.isPending}>
              Leave
            </Button>
          </>
        }
      >
        <p>You lose access at once, and need a new invitation to come back.</p>
      </Dialog>

      {isOwner ? (
        <DeleteDialog isOpen={deleting} onClose={() => setDeleting(false)} onDeleted={gone} />
      ) : null}
    </div>
  );
}

/** "an Admin", "a Member". */
function article(role: string): string {
  return `${/^[AEIOU]/.test(role) ? 'an' : 'a'} ${role.toLowerCase()}`;
}

/** Deletes the workspace once the owner has typed its name. */
function DeleteDialog({
  isOpen,
  onClose,
  onDeleted,
}: {
  isOpen: boolean;
  onClose: () => void;
  onDeleted: () => Promise<void>;
}) {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const [typed, setTyped] = useState('');
  const remove = useMutation({
    mutationFn: () => deleteWorkspace(client, workspace.id),
    onSuccess: onDeleted,
  });

  const close = () => {
    onClose();
    setTyped('');
    remove.reset();
  };

  return (
    <Dialog
      title={`Delete ${workspace.name}?`}
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) close();
      }}
      actions={
        <>
          <Button slot="close" variant="outline">
            Cancel
          </Button>
          <Button
            onPress={() => remove.mutate()}
            isDisabled={typed.trim() !== workspace.name || remove.isPending}
          >
            {remove.isPending ? 'Deleting…' : 'Delete workspace'}
          </Button>
        </>
      }
    >
      <p>
        Every member loses it at once, with everything in it. It can’t be undone. Type the
        workspace’s name to delete it.
      </p>
      <TextField
        label="Workspace name"
        value={typed}
        onChange={setTyped}
        autoComplete="off"
        spellCheck="false"
      />
      <Notice text={remove.error?.message ?? null} />
    </Dialog>
  );
}

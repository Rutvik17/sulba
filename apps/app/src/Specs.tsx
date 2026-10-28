import {
  createSpec,
  criterionKey,
  criterionProblem,
  specKey,
  statusNames,
  titleProblem,
} from '@sulba/data/specs';
import { holds } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from '@tanstack/react-router';
import { type FormEvent, useState } from 'react';
import { useAccount } from './account';
import { ago, momentOf } from './format';
import { Notice } from './Notice';
import styles from './page.module.css';
import { keys, useMembers, useSpecs } from './queries';
import { useWorkspace } from './Shell';
import { useTitle } from './title';

const css = classes(
  styles,
  'page',
  'header',
  'title',
  'count',
  'section',
  'note',
  'scroll',
  'table',
  'key',
  'name',
  'dim',
  'numeric',
  'empty',
  'form',
);

/** Every spec in the workspace, newest first, with its status, criteria and owner. */
export function Specs() {
  const workspace = useWorkspace();
  useTitle('Specs', workspace.name);
  const { data: specs } = useSpecs(workspace);
  const { data: members } = useMembers(workspace);
  const [creating, setCreating] = useState(false);
  const canWrite = holds(workspace.role, 'member');
  const names = new Map(members.map((member) => [member.personId, member.name || member.email]));
  const count = specs.length === 1 ? '1 spec' : `${specs.length} specs`;

  return (
    <div className={css.page}>
      <header className={css.header}>
        <div>
          <h1 className={css.title}>Specs</h1>
          {specs.length ? <p className={css.count}>{count}</p> : null}
        </div>
        {canWrite ? <Button onPress={() => setCreating(true)}>New spec</Button> : null}
      </header>

      {specs.length === 0 ? (
        <section className={css.empty} aria-label="No specs yet">
          <p>
            A spec says what to build, and its acceptance criteria say when it’s done. A test proves
            a criterion by naming its ID, such as <code>{criterionKey(1, 1)}</code>, in its name.
          </p>
          {canWrite ? (
            <Button onPress={() => setCreating(true)}>Write the first spec</Button>
          ) : (
            <p className={css.note}>No one has written a spec here yet.</p>
          )}
        </section>
      ) : (
        <div className={css.scroll}>
          <table className={css.table}>
            <thead>
              <tr>
                <th scope="col">ID</th>
                <th scope="col">Title</th>
                <th scope="col">Status</th>
                <th scope="col">Criteria</th>
                <th scope="col">Owner</th>
                <th scope="col">Updated</th>
              </tr>
            </thead>
            <tbody>
              {specs.map((spec) => {
                const key = specKey(spec.number);
                return (
                  <tr key={spec.id}>
                    <td className={css.key}>{key}</td>
                    <td>
                      <Link
                        to="/$slug/$spec"
                        params={{ slug: workspace.slug, spec: key }}
                        className={css.name}
                      >
                        {spec.title}
                      </Link>
                    </td>
                    <td>{statusNames[spec.status]}</td>
                    <td className={css.numeric}>{spec.criteria}</td>
                    <td>
                      {spec.ownerId ? (
                        (names.get(spec.ownerId) ?? '')
                      ) : (
                        <span className={css.dim}>No owner</span>
                      )}
                    </td>
                    <td className={css.numeric} title={momentOf(spec.updatedAt)}>
                      {ago(spec.updatedAt)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <NewSpec isOpen={creating} onClose={() => setCreating(false)} />
    </div>
  );
}

/** Writes a spec with its title and first acceptance criterion, then opens it. */
function NewSpec({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
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

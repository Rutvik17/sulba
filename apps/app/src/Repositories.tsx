import {
  addRepository,
  branchProblem,
  type Repository,
  removeRepository,
  repositoryProblem,
  setBranch,
} from '@sulba/data/evidence';
import { holds } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { Select } from '@sulba/ui/select';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { type FormEvent, useState } from 'react';
import { useAccount } from './account';
import { Notice } from './Notice';
import styles from './page.module.css';
import { keys, useRepositories } from './queries';
import { useWorkspace } from './Shell';
import { permissions, runners, workflowStep } from './step';

const css = classes(
  styles,
  'section',
  'heading',
  'note',
  'scroll',
  'table',
  'name',
  'dim',
  'actions',
  'card',
  'unseen',
  'steps',
  'step',
  'code',
);

/** The GitHub repositories whose runs send the workspace their test results. Admins add them. */
export function Repositories() {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const { data: repositories } = useRepositories(workspace);
  const isAdmin = holds(workspace.role, 'admin');
  const [name, setName] = useState('');
  const [branch, setBranchName] = useState('main');
  const [checked, setChecked] = useState(false);
  const [removing, setRemoving] = useState<Repository | null>(null);
  const [moving, setMoving] = useState<Repository | null>(null);

  const reread = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: keys.repositories(workspace.id) }),
      queryClient.invalidateQueries({ queryKey: keys.reports(workspace.id) }),
      queryClient.invalidateQueries({ queryKey: keys.proofs(workspace.id) }),
    ]);
  const add = useMutation({
    mutationFn: () => addRepository(client, workspace.id, name, branch),
    onSuccess: async () => {
      setName('');
      setBranchName('main');
      setChecked(false);
      await reread();
    },
  });
  const remove = useMutation({
    mutationFn: (repository: Repository) => removeRepository(client, repository.id),
    onSuccess: async () => {
      setRemoving(null);
      await reread();
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setChecked(true);
    if (repositoryProblem(name) || branchProblem(branch)) return;
    add.mutate();
  };

  return (
    <section className={css.section} aria-labelledby="repositories">
      <h2 id="repositories" className={css.heading}>
        Repositories
      </h2>
      <p className={css.note}>
        Sulba keeps the test results of each repository’s runs on its branch. A run anywhere else,
        such as on a pull request, is answered and not kept.
      </p>
      {repositories.length ? (
        <div className={css.scroll}>
          <table className={css.table}>
            <thead>
              <tr>
                <th scope="col">Repository</th>
                <th scope="col">Branch</th>
                {isAdmin ? (
                  <th scope="col">
                    <span className={css.unseen}>Actions</span>
                  </th>
                ) : null}
              </tr>
            </thead>
            <tbody>
              {repositories.map((repository) => (
                <tr key={repository.id}>
                  <td>
                    <a className={css.name} href={`https://github.com/${repository.name}`}>
                      {repository.name}
                    </a>
                  </td>
                  <td>{repository.branch}</td>
                  {isAdmin ? (
                    <td className={css.actions}>
                      <Button variant="ghost" size="small" onPress={() => setMoving(repository)}>
                        Change branch
                      </Button>
                      <Button variant="ghost" size="small" onPress={() => setRemoving(repository)}>
                        Remove
                      </Button>
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className={css.note}>
          {isAdmin
            ? 'No repositories yet. Add one to take its test results.'
            : 'No repositories yet. An admin or owner adds them.'}
        </p>
      )}

      {isAdmin ? (
        <form className={css.card} onSubmit={submit} noValidate aria-label="Add a repository">
          <TextField
            label="Repository"
            value={name}
            onChange={(value) => {
              setName(value);
              add.reset();
            }}
            placeholder="owner/name"
            error={checked ? repositoryProblem(name) : null}
            autoComplete="off"
            spellCheck="false"
          />
          <TextField
            label="Branch"
            value={branch}
            onChange={setBranchName}
            error={checked ? branchProblem(branch) : null}
            description="Its runs prove criteria. Usually the default branch."
            autoComplete="off"
            spellCheck="false"
          />
          <Notice text={add.error?.message ?? null} />
          <Button type="submit" variant="outline" isDisabled={add.isPending}>
            Add repository
          </Button>
        </form>
      ) : null}

      <Dialog
        title={`Remove ${removing?.name ?? 'the repository'}?`}
        isOpen={removing !== null}
        onOpenChange={(open) => {
          if (!open) setRemoving(null);
        }}
        actions={
          <>
            <Button slot="close" variant="outline">
              Cancel
            </Button>
            <Button
              onPress={() => removing && remove.mutate(removing)}
              isDisabled={remove.isPending}
            >
              Remove
            </Button>
          </>
        }
      >
        <p>
          Its runs’ results are deleted with it, and the criteria they proved are unproven again.
          Its runs’ reports are refused until it’s added again.
        </p>
        <Notice text={remove.error?.message ?? null} />
      </Dialog>

      {moving ? (
        <BranchDialog repository={moving} onClose={() => setMoving(null)} onSaved={reread} />
      ) : null}
    </section>
  );
}

function BranchDialog({
  repository,
  onClose,
  onSaved,
}: {
  repository: Repository;
  onClose: () => void;
  onSaved: () => Promise<unknown>;
}) {
  const { client } = useAccount();
  const [branch, setBranchName] = useState(repository.branch);
  const save = useMutation({
    mutationFn: () => setBranch(client, repository.id, branch),
    onSuccess: async () => {
      await onSaved();
      onClose();
    },
  });
  const problem = branchProblem(branch);

  return (
    <Dialog
      title={`${repository.name}’s branch`}
      isOpen
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
      actions={
        <>
          <Button slot="close" variant="outline">
            Cancel
          </Button>
          <Button
            onPress={() => save.mutate()}
            isDisabled={problem !== null || branch.trim() === repository.branch || save.isPending}
          >
            Save
          </Button>
        </>
      }
    >
      <p>Only the latest runs on this branch prove criteria.</p>
      <TextField
        label="Branch"
        value={branch}
        onChange={setBranchName}
        error={problem}
        autoComplete="off"
        spellCheck="false"
      />
      <Notice text={save.error?.message ?? null} />
    </Dialog>
  );
}

const suiteShape = /^[A-Za-z0-9_.-]{1,64}$/;

/** The step to add to each workflow that runs tests, for the test runner the team uses. */
export function Sending() {
  const workspace = useWorkspace();
  const [runnerId, setRunnerId] = useState(runners[0]?.id ?? 'pytest');
  const [suite, setSuite] = useState('tests');
  const [copied, setCopied] = useState<string | null>(null);
  const runner = runners.find((each) => each.id === runnerId) ?? runners[0];
  if (!runner) return null;
  const suiteProblem = suiteShape.test(suite)
    ? null
    : 'Use at most 64 letters, digits, dots, hyphens and underscores.';
  const step = workflowStep(window.location.origin, workspace.slug, suite || 'tests', runner);

  const copy = async (what: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(what);
    } catch {
      setCopied(null);
    }
  };

  return (
    <section className={css.section} aria-labelledby="sending">
      <h2 id="sending" className={css.heading}>
        Sending test results
      </h2>
      <p className={css.note}>
        Each job that runs tests sends its JUnit XML report with a token GitHub makes for the run.
        The token lasts minutes and is made out to sulba.dev, so the repository keeps no secret.
      </p>
      <div className={css.card}>
        <Select
          label="Test runner"
          options={runners.map(({ id, name }) => ({ id, name }))}
          value={runner.id}
          onChange={(id) => setRunnerId(id)}
        />
        <TextField
          label="Suite"
          value={suite}
          onChange={setSuite}
          error={suiteProblem}
          description="A name for this job’s tests, different in each job."
          autoComplete="off"
          spellCheck="false"
        />
      </div>
      <ol className={css.steps}>
        <li>
          <div className={css.step}>
            <p>Let the job ask GitHub for the run’s token:</p>
            <pre className={css.code}>
              <code>{permissions}</code>
            </pre>
          </div>
        </li>
        <li>
          <div className={css.step}>
            <p>
              Run the tests so they write a report{runner.needs ? `, with ${runner.needs}` : ''}:
            </p>
            <pre className={css.code}>
              <code>{runner.command}</code>
            </pre>
          </div>
        </li>
        <li>
          <div className={css.step}>
            <p>Send it with this step, after the tests. It runs even when they fail:</p>
            <pre className={css.code}>
              <code>{step}</code>
            </pre>
            <Button variant="outline" size="small" onPress={() => void copy('step', step)}>
              {copied === 'step' ? 'Copied' : 'Copy the step'}
            </Button>
          </div>
        </li>
      </ol>
    </section>
  );
}

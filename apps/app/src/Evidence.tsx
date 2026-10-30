import type { CriterionProof, Proof } from '@sulba/data/evidence';
import { criterionKey, specKey } from '@sulba/data/specs';
import { holds } from '@sulba/data/workspaces';
import { classes } from '@sulba/ui/classes';
import { Link } from '@tanstack/react-router';
import { ProofMark } from './ProofMark';
import styles from './page.module.css';
import { commitUrl, proofOrder, reasonOf, reportText, runUrl } from './proofs';
import { useProofs, useReports, useRepositories } from './queries';
import { useWorkspace } from './Shell';
import { useTitle } from './title';
import { When } from './When';

const css = classes(
  styles,
  'page',
  'header',
  'title',
  'count',
  'section',
  'heading',
  'note',
  'scroll',
  'table',
  'key',
  'name',
  'dim',
  'numeric',
  'empty',
  'person',
  'wrap',
);

/** Specs that won't be built prove nothing, so their criteria are left out. */
const settled = new Set(['abandoned', 'superseded']);

/**
 * Every criterion against its latest test results, failing first, then unproven, then proven,
 * and the runs those results come from.
 */
export function Evidence() {
  const workspace = useWorkspace();
  useTitle('Evidence', workspace.name);
  const { data: repositories } = useRepositories(workspace);
  const { data: reports } = useReports(workspace);
  const { data: all } = useProofs(workspace);
  const proofs = all
    .filter((proof) => !settled.has(proof.specStatus))
    .sort(
      (a, b) =>
        proofOrder[a.state] - proofOrder[b.state] ||
        a.specNumber - b.specNumber ||
        a.criterionNumber - b.criterionNumber,
    );
  const counted = (state: Proof) => proofs.filter((proof) => proof.state === state).length;
  const summary = proofs.length
    ? `${proofs.length === 1 ? '1 criterion' : `${proofs.length} criteria`}: ${counted('failing')} failing, ${counted('unproven')} unproven, ${counted('proven')} proven`
    : null;
  const isAdmin = holds(workspace.role, 'admin');

  return (
    <div className={css.page}>
      <header className={css.header}>
        <div>
          <h1 className={css.title}>Evidence</h1>
          {summary ? <p className={css.count}>{summary}</p> : null}
        </div>
      </header>

      {repositories.length === 0 ? (
        <section className={css.empty} aria-label="No evidence yet">
          <p>
            Evidence comes from your CI. Add a GitHub repository, then one step to each workflow
            that runs tests, and every run on its main branch sends its results here. A test proves
            a criterion by naming its ID, such as <code>{criterionKey(1, 1)}</code>.
          </p>
          {isAdmin ? (
            <Link to="/$slug/settings" params={{ slug: workspace.slug }} hash="repositories">
              Add a repository
            </Link>
          ) : (
            <p className={css.note}>An admin or owner adds repositories in Settings.</p>
          )}
        </section>
      ) : reports.length === 0 ? (
        <section className={css.empty} aria-label="No runs yet">
          <p>
            No run has sent its results yet. Settings shows the step to add to each workflow that
            runs tests.
          </p>
          <Link to="/$slug/settings" params={{ slug: workspace.slug }} hash="sending">
            See the step
          </Link>
        </section>
      ) : null}

      <section className={css.section} aria-labelledby="criteria">
        <h2 id="criteria" className={css.heading}>
          Criteria
        </h2>
        {proofs.length ? (
          <div className={css.scroll}>
            <table className={css.table}>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Criterion</th>
                  <th scope="col">Proof</th>
                  <th scope="col">Tests</th>
                  <th scope="col">Last run</th>
                </tr>
              </thead>
              <tbody>
                {proofs.map((proof) => (
                  <Row key={proof.criterionId} proof={proof} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className={css.note}>No spec has criteria yet.</p>
        )}
      </section>

      {reports.length ? (
        <section className={css.section} aria-labelledby="runs">
          <h2 id="runs" className={css.heading}>
            Runs
          </h2>
          <div className={css.scroll}>
            <table className={css.table}>
              <thead>
                <tr>
                  <th scope="col">Repository</th>
                  <th scope="col">Suite</th>
                  <th scope="col">Commit</th>
                  <th scope="col">Run</th>
                  <th scope="col">Tests</th>
                  <th scope="col">Received</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.id}>
                    <td>
                      <span className={css.person}>
                        <span className={css.name}>{report.repository}</span>
                        <span className={css.dim}>{report.branch}</span>
                      </span>
                    </td>
                    <td>{report.suite}</td>
                    <td>
                      <a className={css.key} href={commitUrl(report.repository, report.sha)}>
                        {report.sha.slice(0, 7)}
                      </a>
                    </td>
                    <td>
                      <a href={runUrl(report.repository, report.runId)}>
                        {report.workflow}, run {report.runId}
                      </a>
                    </td>
                    <td className={css.numeric}>{reportText(report)}</td>
                    <td className={css.numeric}>
                      <When at={report.receivedAt} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function Row({ proof }: { proof: CriterionProof }) {
  const workspace = useWorkspace();
  const id = criterionKey(proof.specNumber, proof.criterionNumber);
  const tests = proof.tests
    ? [
        proof.passed ? `${proof.passed} passed` : '',
        proof.failed ? `${proof.failed} failed` : '',
        proof.skipped ? `${proof.skipped} skipped` : '',
      ]
        .filter(Boolean)
        .join(', ')
    : 'None';
  return (
    <tr>
      <td>
        <Link
          to="/$slug/$spec"
          params={{ slug: workspace.slug, spec: specKey(proof.specNumber) }}
          hash={`AC-${proof.criterionNumber}`}
          className={css.key}
        >
          {id}
        </Link>
      </td>
      <td className={css.wrap}>
        <span className={css.person}>
          <span>{proof.text}</span>
          <span className={css.dim}>{proof.specTitle}</span>
        </span>
      </td>
      <td>
        <ProofMark state={proof.state} reason={reasonOf(proof)} />
      </td>
      <td className={css.numeric}>{tests}</td>
      <td className={css.numeric}>
        {proof.checkedAt ? <When at={proof.checkedAt} /> : <span className={css.dim}>Never</span>}
      </td>
    </tr>
  );
}

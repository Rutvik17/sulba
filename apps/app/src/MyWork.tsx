import { actorName, requestKey } from '@sulba/data/requests';
import { standingOf } from '@sulba/data/reviewers';
import { criterionKey, specKey, statusNames } from '@sulba/data/specs';
import { pullRequestName, taskKey, taskStatusNames } from '@sulba/data/tasks';
import { holds } from '@sulba/data/workspaces';
import { classes } from '@sulba/ui/classes';
import { Link } from '@tanstack/react-router';
import { ProofMark } from './ProofMark';
import styles from './page.module.css';
import { reasonOf } from './proofs';
import { useMembers, useWork } from './queries';
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
  'dim',
  'numeric',
  'person',
  'wrap',
);

function counted(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}

/**
 * What needs the signed-in person in the workspace now: the questions agents asked about the open
 * requests they wrote, the tasks handed in or blocked on the specs they own, the specs they've been
 * asked to review, the specs they own that aren't built yet, and the criteria failing on their
 * specs.
 */
export function MyWork() {
  const workspace = useWorkspace();
  useTitle('My work', workspace.name);
  const { data: work } = useWork(workspace);
  const { data: members } = useMembers(workspace);
  const names = new Map(members.map((member) => [member.personId, member.name || member.email]));
  const slug = workspace.slug;
  const summary =
    [
      work.questions.length ? counted(work.questions.length, 'to answer', 'to answer') : '',
      work.tasks.length ? counted(work.tasks.length, 'task to check', 'tasks to check') : '',
      work.asked.length ? counted(work.asked.length, 'to review', 'to review') : '',
      work.owned.length ? counted(work.owned.length, 'open spec', 'open specs') : '',
      work.failing.length
        ? counted(work.failing.length, 'criterion failing', 'criteria failing')
        : '',
    ]
      .filter(Boolean)
      .join(' · ') || 'Nothing needs you right now.';

  return (
    <div className={css.page}>
      <header className={css.header}>
        <div>
          <h1 className={css.title}>My work</h1>
          <p className={css.count}>{summary}</p>
        </div>
      </header>

      {work.questions.length ? (
        <section className={css.section} aria-labelledby="to-answer">
          <h2 id="to-answer" className={css.heading}>
            Questions for you
          </h2>
          <div className={css.scroll}>
            <table className={css.table}>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Question</th>
                  <th scope="col">Asked by</th>
                  <th scope="col">Asked</th>
                </tr>
              </thead>
              <tbody>
                {work.questions.map((question) => (
                  <tr key={question.id}>
                    <td>
                      <Link
                        to="/$slug/$spec"
                        params={{ slug, spec: requestKey(question.requestNumber) }}
                        className={css.key}
                      >
                        {requestKey(question.requestNumber)}
                      </Link>
                    </td>
                    <td className={css.wrap}>
                      <span className={css.person}>
                        <span>{question.text}</span>
                        <span className={css.dim}>{question.requestTitle}</span>
                      </span>
                    </td>
                    <td>
                      {actorName(
                        question.askedBy && names.get(question.askedBy),
                        question.askedByAgent,
                      )}
                    </td>
                    <td className={css.numeric}>
                      <When at={question.askedAt} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {work.tasks.length ? (
        <section className={css.section} aria-labelledby="to-check">
          <h2 id="to-check" className={css.heading}>
            Tasks to check
          </h2>
          <div className={css.scroll}>
            <table className={css.table}>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Task</th>
                  <th scope="col">Status</th>
                  <th scope="col">Taken by</th>
                  <th scope="col">Updated</th>
                </tr>
              </thead>
              <tbody>
                {work.tasks.map((task) => (
                  <tr key={task.id}>
                    <td>
                      <Link
                        to="/$slug/$spec"
                        params={{ slug, spec: taskKey(task.number) }}
                        className={css.key}
                      >
                        {taskKey(task.number)}
                      </Link>
                    </td>
                    <td className={css.wrap}>
                      <span className={css.person}>
                        <span>{task.title}</span>
                        <span className={css.dim}>
                          {task.status === 'blocked'
                            ? `${specKey(task.specNumber)} · ${task.note ?? ''}`
                            : `${specKey(task.specNumber)}${task.pullRequest ? ` · ${pullRequestName(task.pullRequest)}` : ''}`}
                        </span>
                      </span>
                    </td>
                    <td>{taskStatusNames[task.status]}</td>
                    <td>{actorName(task.takenBy && names.get(task.takenBy), task.takenByAgent)}</td>
                    <td className={css.numeric}>
                      <When at={task.updatedAt} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      <section className={css.section} aria-labelledby="to-review">
        <h2 id="to-review" className={css.heading}>
          To review
        </h2>
        {work.asked.length ? (
          <div className={css.scroll}>
            <table className={css.table}>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Spec</th>
                  <th scope="col">Asked by</th>
                  <th scope="col">Asked</th>
                </tr>
              </thead>
              <tbody>
                {work.asked.map((asked) => (
                  <tr key={asked.specId}>
                    <td>
                      <Link
                        to="/$slug/$spec"
                        params={{ slug, spec: specKey(asked.specNumber) }}
                        className={css.key}
                      >
                        {specKey(asked.specNumber)}
                      </Link>
                    </td>
                    <td className={css.wrap}>
                      <span className={css.person}>
                        <span>{asked.specTitle}</span>
                        {asked.changedSinceAnswer ? (
                          <span className={css.dim}>Changed since you asked for changes</span>
                        ) : null}
                      </span>
                    </td>
                    <td>
                      {(asked.requestedBy && names.get(asked.requestedBy)) || (
                        <span className={css.dim}>Someone who has left</span>
                      )}
                    </td>
                    <td className={css.numeric}>
                      <When at={asked.requestedAt} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className={css.note}>Nothing is waiting for your review.</p>
        )}
      </section>

      <section className={css.section} aria-labelledby="your-specs">
        <h2 id="your-specs" className={css.heading}>
          Your specs
        </h2>
        {work.owned.length ? (
          <div className={css.scroll}>
            <table className={css.table}>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Spec</th>
                  <th scope="col">Status</th>
                  <th scope="col">Review</th>
                  <th scope="col">Updated</th>
                </tr>
              </thead>
              <tbody>
                {work.owned.map((spec) => (
                  <tr key={spec.id}>
                    <td>
                      <Link
                        to="/$slug/$spec"
                        params={{ slug, spec: specKey(spec.number) }}
                        className={css.key}
                      >
                        {specKey(spec.number)}
                      </Link>
                    </td>
                    <td className={css.wrap}>{spec.title}</td>
                    <td>{statusNames[spec.status]}</td>
                    <td>
                      {spec.verdicts.length ? (
                        standingOf(spec.verdicts.map((verdict) => ({ verdict })))
                      ) : (
                        <span className={css.dim}>No reviewers</span>
                      )}
                    </td>
                    <td className={css.numeric}>
                      <When at={spec.updatedAt} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className={css.note}>
            You don’t own a spec that’s still to be built.{' '}
            {holds(workspace.role, 'member') ? (
              <Link to="/$slug/specs" params={{ slug }}>
                Write one
              </Link>
            ) : null}
          </p>
        )}
      </section>

      <section className={css.section} aria-labelledby="failing">
        <h2 id="failing" className={css.heading}>
          Failing on your specs
        </h2>
        {work.failing.length ? (
          <div className={css.scroll}>
            <table className={css.table}>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Criterion</th>
                  <th scope="col">Proof</th>
                  <th scope="col">Last run</th>
                </tr>
              </thead>
              <tbody>
                {work.failing.map((proof) => (
                  <tr key={proof.criterionId}>
                    <td>
                      <Link
                        to="/$slug/$spec"
                        params={{ slug, spec: specKey(proof.specNumber) }}
                        hash={`AC-${proof.criterionNumber}`}
                        className={css.key}
                      >
                        {criterionKey(proof.specNumber, proof.criterionNumber)}
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
                    <td className={css.numeric}>
                      {proof.checkedAt ? <When at={proof.checkedAt} /> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className={css.note}>No criterion of your specs is failing.</p>
        )}
      </section>
    </div>
  );
}

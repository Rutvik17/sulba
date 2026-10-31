import {
  actorName,
  answerProblem,
  answerQuestion,
  type Question,
  type Request,
  type RequestChange,
  requestKey,
  requestStatuses,
  requestStatusMeanings,
  requestStatusNames,
  requestTitleProblem,
  updateRequest,
} from '@sulba/data/requests';
import { specKey, statusNames } from '@sulba/data/specs';
import { holds, type Member } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Select } from '@sulba/ui/select';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import { type FormEvent, useState } from 'react';
import { useAccount } from './account';
import { useCommands } from './commands';
import { EditableTitle, SavedText } from './Editing';
import { Notice } from './Notice';
import { keys, useMembers, useRequestAt } from './queries';
import ownStyles from './request.module.css';
import { useWorkspace } from './Shell';
import styles from './spec.module.css';
import { useTitle } from './title';
import { When } from './When';

const css = classes(
  styles,
  'spec',
  'head',
  'main',
  'side',
  'crumbs',
  'key',
  'title',
  'heading',
  'section',
  'note',
  'facts',
  'unseen',
);
const own = classes(
  ownStyles,
  'questions',
  'question',
  'asked',
  'by',
  'answer',
  'answered',
  'waiting',
  'reply',
  'drafted',
  'spec',
  'status',
);

/**
 * A request's page, at its ID: REQ-3 (decision record 60). Its writer's words, the questions
 * agents asked about it with the answers people gave, and the specs drafted from it.
 */
export function RequestPage({ number }: { number: number }) {
  const workspace = useWorkspace();
  const { data: request } = useRequestAt(workspace, number);
  const { data: members } = useMembers(workspace);
  if (!request) return <NoRequest number={number} />;
  return <Page request={request} members={members} />;
}

function NoRequest({ number }: { number: number }) {
  const workspace = useWorkspace();
  useTitle('No request here', workspace.name);
  return (
    <div className={css.main}>
      <h1 className={css.title}>No request here</h1>
      <p className={css.note}>{`${requestKey(number)} hasn’t been written in this workspace.`}</p>
      <Link to="/$slug/requests" params={{ slug: workspace.slug }}>
        Go to the requests
      </Link>
    </div>
  );
}

function Page({ request, members }: { request: Request; members: readonly Member[] }) {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const canWrite = holds(workspace.role, 'member');
  const key = requestKey(request.number);
  useTitle(`${key} ${request.title}`, workspace.name);
  const [failure, setFailure] = useState<string | null>(null);
  const names = new Map(members.map((member) => [member.personId, member.name || member.email]));

  const reread = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: keys.request(workspace.id, request.number) }),
      queryClient.invalidateQueries({ queryKey: keys.requests(workspace.id) }),
      queryClient.invalidateQueries({ queryKey: keys.work(workspace.id) }),
    ]);
  const change = useMutation({
    mutationFn: (patch: RequestChange) => updateRequest(client, request.id, patch),
    onMutate: () => setFailure(null),
    onSuccess: reread,
    onError: (error) => setFailure(error.message),
  });

  useCommands(
    canWrite
      ? [
          {
            id: 'request-status',
            label: 'Change status',
            group: key,
            keys: ['s'],
            does: {
              title: 'Change status',
              actions: requestStatuses.map((status) => ({
                id: status,
                label: requestStatusNames[status],
                ...(status === request.status ? { note: 'Current' } : {}),
                run: () => change.mutate({ status }),
              })),
            },
          },
        ]
      : [],
  );

  return (
    <div className={css.spec}>
      <div className={css.head}>
        <nav aria-label="Breadcrumb" className={css.crumbs}>
          <Link to="/$slug/requests" params={{ slug: workspace.slug }}>
            Requests
          </Link>
          <span aria-hidden="true">/</span>
          <span className={css.key}>{key}</span>
        </nav>
        <EditableTitle
          title={request.title}
          canWrite={canWrite}
          problemOf={requestTitleProblem}
          onSave={(title) => change.mutate({ title })}
        />
        <Notice text={failure} />
      </div>

      <div className={css.main}>
        <section className={css.section} aria-labelledby="text">
          <h2 id="text" className={css.unseen}>
            Text
          </h2>
          <SavedText
            text={request.body}
            label={`${key}’s text`}
            placeholder="Who it’s for, what they should be able to do, and anything it must work with. Markdown works here."
            canWrite={canWrite}
            save={async (body) => {
              await updateRequest(client, request.id, { body });
            }}
          />
        </section>

        <section className={css.section} aria-labelledby="questions">
          <h2 id="questions" className={css.heading}>
            Questions
          </h2>
          {request.questions.length === 0 ? (
            <p className={css.note}>
              No questions yet. A connected agent asks here what it needs to know before it drafts
              the specs.
            </p>
          ) : (
            <ol className={own.questions}>
              {request.questions.map((question) => (
                <Asked
                  key={question.id}
                  question={question}
                  names={names}
                  canAnswer={canWrite && request.status === 'open'}
                  onAnswered={reread}
                />
              ))}
            </ol>
          )}
        </section>

        <section className={css.section} aria-labelledby="drafted">
          <h2 id="drafted" className={css.heading}>
            Specs
          </h2>
          {request.specs.length === 0 ? (
            <p className={css.note}>No specs drafted from it yet.</p>
          ) : (
            <ul className={own.drafted}>
              {request.specs.map((spec) => (
                <li key={spec.number} className={own.spec}>
                  <span className={css.key}>{specKey(spec.number)}</span>
                  <Link
                    to="/$slug/$spec"
                    params={{ slug: workspace.slug, spec: specKey(spec.number) }}
                  >
                    {spec.title}
                  </Link>
                  <span className={own.status}>{statusNames[spec.status]}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <aside className={css.side} aria-label="Details">
        <dl className={css.facts}>
          <div>
            <dt>Status</dt>
            <dd>
              {canWrite ? (
                <Select
                  label="Status"
                  hideLabel
                  size="small"
                  options={requestStatuses.map((id) => ({
                    id,
                    name: requestStatusNames[id],
                    description: requestStatusMeanings[id],
                  }))}
                  value={request.status}
                  onChange={(status) => change.mutate({ status })}
                  isDisabled={change.isPending}
                />
              ) : (
                requestStatusNames[request.status]
              )}
            </dd>
          </div>
          <div>
            <dt>Writer</dt>
            <dd>{(request.createdBy && names.get(request.createdBy)) || 'Someone who has left'}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>
              <When at={request.createdAt} day />
            </dd>
          </div>
          <div>
            <dt>Updated</dt>
            <dd>
              <When at={request.updatedAt} />
            </dd>
          </div>
        </dl>
      </aside>
    </div>
  );
}

/** A question, with its answer, or the field a member answers it in. */
function Asked({
  question,
  names,
  canAnswer,
  onAnswered,
}: {
  question: Question;
  names: ReadonlyMap<string, string | null>;
  canAnswer: boolean;
  onAnswered: () => Promise<unknown>;
}) {
  const { client } = useAccount();
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(question.answer ?? '');
  const [checked, setChecked] = useState(false);
  const answer = useMutation({
    mutationFn: () => answerQuestion(client, question.id, text),
    onSuccess: async () => {
      setEditing(false);
      setChecked(false);
      await onAnswered();
    },
  });
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setChecked(true);
    if (answerProblem(text)) return;
    answer.mutate();
  };
  const answering = canAnswer && (question.answer === null || editing);

  return (
    <li className={own.question}>
      <p className={own.asked}>{question.text}</p>
      <p className={own.by}>
        {actorName(question.askedBy && names.get(question.askedBy), question.askedByAgent)} ·{' '}
        <When at={question.askedAt} />
      </p>
      {answering ? (
        <form className={own.reply} onSubmit={submit} noValidate>
          <TextField
            label="Your answer"
            value={text}
            onChange={setText}
            multiline
            error={checked ? answerProblem(text) : null}
          />
          <Notice text={answer.error?.message ?? null} />
          <div>
            <Button type="submit" size="small" isDisabled={answer.isPending}>
              {answer.isPending ? 'Saving…' : 'Answer'}
            </Button>
            {editing ? (
              <Button variant="ghost" size="small" onPress={() => setEditing(false)}>
                Cancel
              </Button>
            ) : null}
          </div>
        </form>
      ) : question.answer === null ? (
        <p className={own.waiting}>Waiting for an answer</p>
      ) : (
        <>
          <p className={own.answer}>{question.answer}</p>
          <div className={own.answered}>
            <p className={own.by}>
              {(question.answeredBy && names.get(question.answeredBy)) || 'Someone who has left'}
              {question.answeredAt ? (
                <>
                  {' · '}
                  <When at={question.answeredAt} />
                </>
              ) : null}
            </p>
            {canAnswer ? (
              <Button variant="ghost" size="small" onPress={() => setEditing(true)}>
                Change answer
              </Button>
            ) : null}
          </div>
        </>
      )}
    </li>
  );
}

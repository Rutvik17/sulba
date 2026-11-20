import type { Request } from '@sulba/data/requests';
import {
  type AgentRun,
  type AgentRunStatus,
  agentJobs,
  agentNames,
  checkRun,
  dollars,
  type Spending,
  startRun,
} from '@sulba/data/runs';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { useAccount } from './account';
import { Notice } from './Notice';
import { keys, useRuns, useSpending } from './queries';
import ownStyles from './request.module.css';
import { useWorkspace } from './Shell';
import styles from './spec.module.css';
import { When } from './When';

const css = classes(styles, 'section', 'heading', 'note', 'key');
const own = classes(ownStyles, 'drafted', 'agent', 'asked', 'by', 'run', 'made', 'status');

const statusNames: Record<Exclude<AgentRunStatus, 'running'>, string> = {
  done: 'Done',
  failed: 'Failed',
  stopped: 'Stopped',
};

/** How often the page asks the Worker to check a run that's still working. */
const CHECK_EVERY = 15_000;

/** The month's spending, in a sentence. */
function spent({ limitCents, spentCents, reservedCents }: Spending): string {
  if (limitCents === 0) return 'This workspace has no allowance for Sulba’s agents yet.';
  const used = `${dollars(spentCents)} of this month’s ${dollars(limitCents)} spent`;
  return reservedCents > 0
    ? `${used}, and ${dollars(reservedCents)} set aside while an agent works.`
    : `${used}.`;
}

/**
 * Sulba's agents on a request's page (decision records 63 and 64): what Intake does, the button a
 * member starts it with, the month's spending against the workspace's limit, and each run with
 * what it did and what it cost. While a run works, the page asks the Worker to check it, so it
 * settles even when Anthropic's notice is lost, and reads the request again once it has.
 */
export function AgentRuns({ request, canWrite }: { request: Request; canWrite: boolean }) {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const { data: runs } = useRuns(request.id);
  const { data: spending } = useSpending(workspace);
  const working = runs.find((run) => run.status === 'running');
  const left = spending.limitCents - spending.spentCents - spending.reservedCents;

  const reread = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: keys.runs(request.id) }),
      queryClient.invalidateQueries({ queryKey: keys.spending(workspace.id) }),
    ]);

  const workingId = working?.id;
  useEffect(() => {
    if (!workingId) return;
    const timer = setInterval(() => {
      checkRun(client, workingId).then(
        () => queryClient.invalidateQueries({ queryKey: keys.runs(request.id) }),
        () => undefined,
      );
    }, CHECK_EVERY);
    return () => clearInterval(timer);
  }, [client, workingId, queryClient, request.id]);

  // Once a run stops working, its questions are on the request and its cost is spent.
  const watched = useRef(workingId);
  useEffect(() => {
    if (watched.current && !workingId) {
      queryClient.invalidateQueries({ queryKey: keys.request(workspace.id, request.number) });
      queryClient.invalidateQueries({ queryKey: keys.spending(workspace.id) });
      queryClient.invalidateQueries({ queryKey: keys.work(workspace.id) });
    }
    watched.current = workingId;
  }, [workingId, queryClient, workspace.id, request.number]);

  const begin = useMutation({
    mutationFn: () => startRun(client, request.id, 'intake'),
    onSuccess: reread,
  });

  return (
    <section className={css.section} aria-labelledby="agents">
      <h2 id="agents" className={css.heading}>
        Sulba’s agents
      </h2>
      <div className={own.agent}>
        <div className={own.made}>
          <span className={own.asked}>{agentNames.intake}</span>
          <span className={own.by}>{agentJobs.intake}</span>
        </div>
        {canWrite && request.status === 'open' ? (
          <Button
            size="small"
            variant="outline"
            isDisabled={Boolean(working) || begin.isPending || left < 10}
            onPress={() => begin.mutate()}
          >
            {working ? 'Working…' : begin.isPending ? 'Starting…' : `Ask ${agentNames.intake}`}
          </Button>
        ) : null}
      </div>
      <p className={css.note}>{spent(spending)}</p>
      <Notice text={begin.error?.message ?? null} />
      {runs.length ? (
        <ul className={own.drafted} aria-label="Runs">
          {runs.map((run) => (
            <Run key={run.id} run={run} />
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function Run({ run }: { run: AgentRun }) {
  return (
    <li className={own.run}>
      <span className={css.key}>{agentNames[run.role]}</span>
      <span className={own.made}>
        <span>
          {run.status === 'running' ? 'Working on it.' : (run.note ?? statusNames[run.status])}
        </span>
        <span className={own.by}>
          {run.status === 'running' ? (
            <>
              Started <When at={run.startedAt} /> · up to {dollars(run.budgetCents)}
            </>
          ) : (
            <>
              {statusNames[run.status]} · <When at={run.startedAt} /> · {dollars(run.costCents)}
            </>
          )}
        </span>
      </span>
    </li>
  );
}

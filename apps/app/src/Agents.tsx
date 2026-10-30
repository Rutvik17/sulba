import { type Agent, agentsOf, disconnect } from '@sulba/data/agents';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { Select } from '@sulba/ui/select';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useAccount } from './account';
import { Notice } from './Notice';
import styles from './page.module.css';
import { keys } from './queries';
import { setups } from './setups';
import { When } from './When';

const css = classes(
  styles,
  'section',
  'heading',
  'note',
  'card',
  'scroll',
  'table',
  'name',
  'dim',
  'actions',
  'unseen',
  'steps',
  'step',
  'code',
);

/**
 * How to connect a coding agent to Sulba's MCP server, and the agents the person has connected,
 * each of which they can disconnect (decision record 51). A connection is the person's, so it
 * reaches every workspace they're in.
 */
export function Agents() {
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const all = setups(window.location.origin);
  const [chosen, setChosen] = useState(all[0]?.id ?? '');
  const [copied, setCopied] = useState<string | null>(null);
  const [leaving, setLeaving] = useState<Agent | null>(null);
  const setup = all.find((each) => each.id === chosen) ?? all[0];

  const agents = useQuery({ queryKey: keys.agents, queryFn: () => agentsOf(client) });
  const remove = useMutation({
    mutationFn: (agent: Agent) => disconnect(client, agent.clientId),
    onSuccess: async () => {
      setLeaving(null);
      await queryClient.invalidateQueries({ queryKey: keys.agents });
    },
  });

  const copy = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(code);
    } catch {
      setCopied(null);
    }
  };

  return (
    <section className={css.section} aria-labelledby="agents">
      <h2 id="agents" className={css.heading}>
        Agents
      </h2>
      <p className={css.note}>
        Coding agents connect to Sulba through MCP and sign in as you. Each one works in every
        workspace you’re in, within your role, and each spec’s history shows its changes as its own.
      </p>
      {setup ? (
        <div className={css.card}>
          <Select
            label="Agent"
            options={all.map(({ id, name }) => ({ id, name }))}
            value={setup.id}
            onChange={setChosen}
          />
          <ol className={css.steps}>
            {setup.steps.map((step) => (
              <li key={step.text}>
                <div className={css.step}>
                  <p>{step.text}</p>
                  {step.code ? (
                    <>
                      <pre className={css.code}>
                        <code>{step.code}</code>
                      </pre>
                      <Button
                        variant="outline"
                        size="small"
                        onPress={() => void copy(step.code ?? '')}
                      >
                        {copied === step.code ? 'Copied' : 'Copy'}
                      </Button>
                    </>
                  ) : null}
                </div>
              </li>
            ))}
          </ol>
        </div>
      ) : null}

      <h3 className={css.heading}>Connected</h3>
      {agents.isError ? (
        <Notice text={agents.error.message} />
      ) : agents.data?.length ? (
        <div className={css.scroll}>
          <table className={css.table}>
            <thead>
              <tr>
                <th scope="col">Agent</th>
                <th scope="col">Connected</th>
                <th scope="col">
                  <span className={css.unseen}>Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {agents.data.map((agent) => (
                <tr key={agent.clientId}>
                  <td className={css.name}>{agent.name}</td>
                  <td className={css.dim}>
                    <When at={agent.connectedAt} day />
                  </td>
                  <td className={css.actions}>
                    <Button variant="ghost" size="small" onPress={() => setLeaving(agent)}>
                      Disconnect
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : agents.data ? (
        <p className={css.note}>No agents are connected yet.</p>
      ) : null}

      <Dialog
        title={`Disconnect ${leaving?.name ?? 'the agent'}?`}
        isOpen={leaving !== null}
        onOpenChange={(open) => {
          if (!open) setLeaving(null);
        }}
        actions={
          <>
            <Button slot="close" variant="outline">
              Cancel
            </Button>
            <Button onPress={() => leaving && remove.mutate(leaving)} isDisabled={remove.isPending}>
              Disconnect
            </Button>
          </>
        }
      >
        <p>
          It stops acting for you at once, in every workspace. Connecting it again asks you again.
        </p>
        <Notice text={remove.error?.message ?? null} />
      </Dialog>
    </section>
  );
}

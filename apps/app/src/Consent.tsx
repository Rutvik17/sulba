import { answer, requestOf } from '@sulba/data/agents';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Link, useSearch } from '@tanstack/react-router';
import { useEffect } from 'react';
import { useAccount } from './account';
import { Centered } from './Centered';
import styles from './Consent.module.css';
import { Notice } from './Notice';

const css = classes(styles, 'terms', 'actions', 'where');

/**
 * Where an agent's request to act for the person leads, from Supabase's OAuth server: who is
 * asking, what it may and may not do, and where answering sends the person back to (decision
 * record 51). An agent allowed before is sent straight back.
 */
export function Consent() {
  const { authorization_id: id } = useSearch({ from: '/oauth/consent' });
  const { client, email } = useAccount();

  const asked = useQuery({
    queryKey: ['consent', id],
    queryFn: () => requestOf(client, id),
    enabled: id !== '',
    retry: false,
  });
  const decide = useMutation({
    mutationFn: (allow: boolean) => answer(client, id, allow),
    onSuccess: (redirectTo) => window.location.assign(redirectTo),
  });
  const before = asked.data && 'redirectTo' in asked.data ? asked.data.redirectTo : null;
  useEffect(() => {
    if (before) window.location.replace(before);
  }, [before]);

  if (id === '') {
    return (
      <Centered
        title="This link is incomplete"
        lead="Connect again from your agent, which opens this page with its request."
      >
        <Link to="/">Go to Sulba</Link>
      </Centered>
    );
  }
  if (asked.isError) {
    return (
      <Centered title="This request can’t be answered" lead={asked.error.message}>
        <Link to="/">Go to Sulba</Link>
      </Centered>
    );
  }
  if (!asked.data || !('request' in asked.data)) return null;

  const { agent, returnTo } = asked.data.request;
  const back = URL.canParse(returnTo) ? new URL(returnTo).host : returnTo;
  return (
    <Centered
      title={`Connect ${agent} to Sulba?`}
      tab="Connect an agent"
      lead={`${agent} will act for you${email ? `, ${email},` : ''} in every workspace you’re in, within your role.`}
    >
      <ul className={css.terms}>
        <li>
          It can read specs and their evidence, write specs and criteria, put a spec in review and
          mark it implemented. Each spec’s history shows its changes as its own.
        </li>
        <li>
          It can’t approve, abandon or supersede a spec, confirm a criterion’s tests, remove a
          criterion, or change a workspace’s people, repositories or settings.
        </li>
        <li>You can disconnect it in any workspace’s Settings.</li>
      </ul>
      <Notice text={decide.error?.message ?? null} />
      <div className={css.actions}>
        <Button onPress={() => decide.mutate(true)} isDisabled={decide.isPending}>
          Allow
        </Button>
        <Button
          variant="outline"
          onPress={() => decide.mutate(false)}
          isDisabled={decide.isPending}
        >
          Deny
        </Button>
      </div>
      <p className={css.where}>Either way, you go back to {back}.</p>
    </Centered>
  );
}

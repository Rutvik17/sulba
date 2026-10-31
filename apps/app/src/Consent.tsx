import { answer, type Destination, destinationOf, requestOf } from '@sulba/data/agents';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Link, useSearch } from '@tanstack/react-router';
import { useEffect } from 'react';
import { useAccount, useSignOut } from './account';
import { Centered } from './Centered';
import styles from './Consent.module.css';
import { Notice } from './Notice';

const css = classes(
  styles,
  'account',
  'request',
  'agent',
  'where',
  'check',
  'scopes',
  'scope',
  'list',
  'yes',
  'no',
  'note',
  'actions',
);

/** Where allowing returns the person to, and when to allow it. */
function placeOf(
  destination: Exclude<Destination, { kind: 'refused' }>,
  agent: string,
): [string, string] {
  switch (destination.kind) {
    case 'computer':
      return [
        `${destination.address} on this computer`,
        `Only allow this if you just started connecting ${agent} on this computer.`,
      ];
    case 'app':
      return [
        `the app that opens ${destination.scheme}:// links`,
        `Only allow this if you just started connecting ${agent} from that app.`,
      ];
    case 'website':
      return [
        destination.host,
        `Only allow this if you just started connecting ${agent} on ${destination.host}.`,
      ];
  }
}

function Yes() {
  return (
    <svg className={css.yes} viewBox="0 0 16 16" aria-hidden="true">
      <path d="m3.5 8.5 3 3 6-7" />
    </svg>
  );
}

function No() {
  return (
    <svg className={css.no} viewBox="0 0 16 16" aria-hidden="true">
      <path d="m4.5 4.5 7 7m0-7-7 7" />
    </svg>
  );
}

/**
 * Where an agent's request to act for the person leads, from Supabase's OAuth server: who is
 * asking, where allowing returns them, and what it may and may not do (decision record 51). An
 * agent names itself, so the page leads with where it returns the person, and refuses an address
 * that is neither an app on their computer nor a website on HTTPS (decision records 56 and 58). An
 * agent allowed before is sent straight back.
 */
export function Consent() {
  const { authorization_id: id } = useSearch({ from: '/oauth/consent' });
  const { client, email } = useAccount();
  const signOut = useSignOut();

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
  const destination = !asked.data
    ? null
    : 'request' in asked.data
      ? asked.data.request.destination
      : destinationOf(asked.data.redirectTo);
  const before =
    asked.data && 'redirectTo' in asked.data && destination?.kind !== 'refused'
      ? asked.data.redirectTo
      : null;
  useEffect(() => {
    if (before) window.location.replace(before);
  }, [before]);

  if (id === '') {
    return (
      <Centered
        title="This link is incomplete"
        lead="Start connecting again from your agent. It opens this page with its request."
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
  if (destination?.kind === 'refused') {
    return (
      <Centered
        title="This agent can’t be connected"
        lead={`It asked to return you to ${destination.address}. Sulba only returns you to an app on this computer or to a website over HTTPS.`}
      >
        <Link to="/">Go to Sulba</Link>
      </Centered>
    );
  }
  if (!asked.data || !('request' in asked.data) || destination === null) return null;

  const { agent } = asked.data.request;
  const [place, check] = placeOf(destination, agent);
  return (
    <Centered
      title={`Connect ${agent} to Sulba`}
      tab="Connect an agent"
      lead={
        <span className={css.account}>
          {email ? `Signed in as ${email}.` : null}
          <Button variant="ghost" size="small" onPress={() => void signOut()}>
            Use another account
          </Button>
        </span>
      }
    >
      <section className={css.request} aria-label="Request">
        <p className={css.agent}>{agent}</p>
        <p className={css.where}>
          Returns you to <strong>{place}</strong>
        </p>
        <p className={css.check}>{check}</p>
      </section>
      <div className={css.scopes}>
        <section className={css.scope} aria-labelledby="can">
          <h2 id="can">It will be able to</h2>
          <ul className={css.list}>
            <li>
              <Yes />
              Read requests, specs and their test evidence
            </li>
            <li>
              <Yes />
              Ask you questions about a request
            </li>
            <li>
              <Yes />
              Write specs and acceptance criteria
            </li>
            <li>
              <Yes />
              Send specs for review and mark them implemented
            </li>
          </ul>
        </section>
        <section className={css.scope} aria-labelledby="cannot">
          <h2 id="cannot">It won’t be able to</h2>
          <ul className={css.list}>
            <li>
              <No />
              Write or change requests, or answer questions about them
            </li>
            <li>
              <No />
              Approve, abandon or supersede specs
            </li>
            <li>
              <No />
              Remove criteria, or confirm a reworded criterion’s tests
            </li>
            <li>
              <No />
              Change members, repositories or workspace settings
            </li>
          </ul>
        </section>
      </div>
      <p className={css.note}>
        It works in every workspace you’re in, with your role there, and each spec’s history marks
        the changes it makes. You can disconnect it at any time in Settings.
      </p>
      <Notice text={decide.error?.message ?? null} />
      <div className={css.actions}>
        <Button
          variant="outline"
          onPress={() => decide.mutate(false)}
          isDisabled={decide.isPending}
        >
          Cancel
        </Button>
        <Button onPress={() => decide.mutate(true)} isDisabled={decide.isPending}>
          Allow
        </Button>
      </div>
    </Centered>
  );
}

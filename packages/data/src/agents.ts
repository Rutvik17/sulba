// The coding agents a person connects to Sulba, through Supabase's OAuth 2.1 server (decision
// record 51). An agent asks to act for the person, who allows it on the app's consent page; it
// then works in every workspace they're in until they disconnect it.
import type { Client } from './client.ts';
import { Refusal } from './refusal.ts';

/** An agent the person has allowed to act for them. */
export interface Agent {
  readonly clientId: string;
  /** The name it gave when it registered, such as "Claude Code". */
  readonly name: string;
  readonly connectedAt: string;
}

/** An agent asking to act for the person, as the consent page shows it. */
export interface Request {
  readonly id: string;
  readonly agent: string;
  /** Where the person goes back to once they answer: the agent's own address. */
  readonly returnTo: string;
}

/** What the consent page has to show: a request, or the agent's address when it was allowed before. */
export type Asked = { readonly request: Request } | { readonly redirectTo: string };

const failed = 'Sulba couldn’t reach its sign-in service. Try again.';

/** The agents the person has connected, newest first. */
export async function agentsOf(client: Client): Promise<Agent[]> {
  const { data, error } = await client.auth.oauth.listGrants();
  if (error) throw new Refusal(failed);
  return data
    .map((grant) => ({
      clientId: grant.client.id,
      name: grant.client.name || 'An unnamed agent',
      connectedAt: grant.granted_at,
    }))
    .sort((a, b) => b.connectedAt.localeCompare(a.connectedAt));
}

/** Stops an agent acting for the person: its tokens stop working and it has to ask again. */
export async function disconnect(client: Client, clientId: string): Promise<void> {
  const { error } = await client.auth.oauth.revokeGrant({ clientId });
  if (error) throw new Refusal(failed);
}

/** The request an authorization ID names. */
export async function requestOf(client: Client, id: string): Promise<Asked> {
  const { data, error } = await client.auth.oauth.getAuthorizationDetails(id);
  if (error) {
    throw new Refusal(
      'This request has expired or was already answered. Connect again from your agent.',
    );
  }
  if (!('authorization_id' in data)) return { redirectTo: data.redirect_url };
  return {
    request: {
      id: data.authorization_id,
      agent: data.client.name || 'An unnamed agent',
      returnTo: data.redirect_uri,
    },
  };
}

/** Allows or denies the request, and gives the agent's address to go back to. */
export async function answer(client: Client, id: string, allow: boolean): Promise<string> {
  const options = { skipBrowserRedirect: true };
  const { data, error } = allow
    ? await client.auth.oauth.approveAuthorization(id, options)
    : await client.auth.oauth.denyAuthorization(id, options);
  if (error) throw new Refusal(failed);
  return data.redirect_url;
}

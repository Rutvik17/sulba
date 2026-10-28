// The signed-in person and the app's connection to Supabase, which every page reads from here.
// supabase-js loads only once the browser holds a session, or once a page needs Supabase without
// one, such as an invitation link opened before signing in.
import type { Client } from '@sulba/data/client';
import { hasSession, localStore } from '@sulba/data/session';
import { createContext, type ReactNode, use, useEffect, useState } from 'react';

export interface Account {
  readonly client: Client;
  readonly personId: string;
  readonly email: string | null;
}

type State =
  | { readonly state: 'loading' }
  | { readonly state: 'out' }
  | { readonly state: 'in'; readonly account: Account };

interface Accounts {
  readonly state: State;
  readonly signOut: () => Promise<void>;
}

const AccountsContext = createContext<Accounts | null>(null);

/** The app's one connection to Supabase, loaded the first time a page asks for it. */
export async function connection(): Promise<Client> {
  const { supabase } = await import('./supabase');
  return supabase();
}

async function signedIn(): Promise<Account | null> {
  const client = await connection();
  const { data } = await client.auth.getSession();
  const user = data.session?.user;
  return user ? { client, personId: user.id, email: user.email ?? null } : null;
}

/** Knows whether someone is signed in, for the whole app. */
export function AccountProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>(() =>
    hasSession(localStore()) ? { state: 'loading' } : { state: 'out' },
  );

  useEffect(() => {
    if (state.state !== 'loading') return;
    signedIn().then(
      (account) => setState(account ? { state: 'in', account } : { state: 'out' }),
      () => setState({ state: 'out' }),
    );
  }, [state.state]);

  const signOut = async () => {
    if (state.state !== 'in') return;
    const { signOut: end } = await import('@sulba/data/account');
    await end(state.account.client);
    setState({ state: 'out' });
  };

  return <AccountsContext value={{ state, signOut }}>{children}</AccountsContext>;
}

function useAccounts(): Accounts {
  const accounts = use(AccountsContext);
  if (!accounts) throw new Error('The app renders inside AccountProvider');
  return accounts;
}

/** Whether someone is signed in: still finding out, no one, or who. */
export function useAccountState(): State {
  return useAccounts().state;
}

export function useSignOut(): () => Promise<void> {
  return useAccounts().signOut;
}

const SignedInContext = createContext<Account | null>(null);

/** The signed-in person, on a page inside RequireAccount. */
export function useAccount(): Account {
  const account = use(SignedInContext);
  if (!account) throw new Error('useAccount is for pages inside RequireAccount');
  return account;
}

/**
 * Renders its page once someone is signed in, and `signIn` when no one is. While the browser
 * is still finding out, it renders nothing, so no page flashes the wrong state.
 */
export function RequireAccount({ children, signIn }: { children: ReactNode; signIn: ReactNode }) {
  const state = useAccountState();
  if (state.state === 'loading') return null;
  if (state.state === 'out') return signIn;
  return <SignedInContext value={state.account}>{children}</SignedInContext>;
}

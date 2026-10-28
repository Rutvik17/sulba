// What the app reads from Supabase, cached by TanStack Query so pages share it, and the keys a
// change invalidates so every page that shows it reads it again.
import { historyOf, specAt, specsOf } from '@sulba/data/specs';
import {
  invitationsOf,
  membersOf,
  type Workspace,
  workspaceAt,
  workspacesOf,
} from '@sulba/data/workspaces';
import { useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { useAccount } from './account';

export const keys = {
  workspaces: ['workspaces'] as const,
  workspace: (slug: string) => ['workspace', slug] as const,
  members: (workspaceId: string) => ['members', workspaceId] as const,
  invitations: (workspaceId: string) => ['invitations', workspaceId] as const,
  specs: (workspaceId: string) => ['specs', workspaceId] as const,
  spec: (workspaceId: string, number: number) => ['spec', workspaceId, number] as const,
  history: (specId: string) => ['history', specId] as const,
};

/** The workspaces the signed-in person is in. */
export function useWorkspaces() {
  const { client, personId } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.workspaces,
    queryFn: () => workspacesOf(client, personId),
  });
}

/** The workspace at an address, or null when the person isn't in one there. */
export function useWorkspaceAt(slug: string) {
  const { client, personId } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.workspace(slug),
    queryFn: () => workspaceAt(client, personId, slug),
  });
}

export function useMembers(workspace: Workspace) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.members(workspace.id),
    queryFn: () => membersOf(client, workspace.id),
  });
}

/** The links that can still be used. Only admins and owners can see them, so others ask nothing. */
export function useInvitations(workspace: Workspace, canSee: boolean) {
  const { client } = useAccount();
  return useQuery({
    queryKey: keys.invitations(workspace.id),
    queryFn: () => invitationsOf(client, workspace.id),
    enabled: canSee,
  });
}

export function useSpecs(workspace: Workspace) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.specs(workspace.id),
    queryFn: () => specsOf(client, workspace.id),
  });
}

/** The spec with a number in the workspace, or null when there's none. */
export function useSpecAt(workspace: Workspace, number: number) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.spec(workspace.id, number),
    queryFn: () => specAt(client, workspace.id, number),
  });
}

export function useHistory(workspace: Workspace, specId: string) {
  const { client } = useAccount();
  return useQuery({
    queryKey: keys.history(specId),
    queryFn: () => historyOf(client, workspace.id, specId),
  });
}

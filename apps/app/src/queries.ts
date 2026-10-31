// What the app reads from Supabase, cached by TanStack Query so pages share it, and the keys a
// change invalidates so every page that shows it reads it again.
import {
  claimsOfSpec,
  proofsOf,
  proofsOfSpec,
  reportsOf,
  repositoriesOf,
  specProofsOf,
} from '@sulba/data/evidence';
import { requestAt, requestsOf } from '@sulba/data/requests';
import { reviewsOf } from '@sulba/data/reviewers';
import { historyOf, specAt, specsOf } from '@sulba/data/specs';
import { specTasks, taskAt, tasksOf } from '@sulba/data/tasks';
import { workOf } from '@sulba/data/work';
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
  /** The agents the person has connected, which reach every workspace they're in. */
  agents: ['agents'] as const,
  workspace: (slug: string) => ['workspace', slug] as const,
  members: (workspaceId: string) => ['members', workspaceId] as const,
  invitations: (workspaceId: string) => ['invitations', workspaceId] as const,
  requests: (workspaceId: string) => ['requests', workspaceId] as const,
  request: (workspaceId: string, number: number) => ['request', workspaceId, number] as const,
  /** Every task in a workspace; a spec's own sit under it. */
  tasks: (workspaceId: string) => ['tasks', workspaceId] as const,
  specTasks: (workspaceId: string, specId: string) => ['tasks', workspaceId, specId] as const,
  task: (workspaceId: string, number: number) => ['task', workspaceId, number] as const,
  specs: (workspaceId: string) => ['specs', workspaceId] as const,
  spec: (workspaceId: string, number: number) => ['spec', workspaceId, number] as const,
  history: (specId: string) => ['history', specId] as const,
  reviews: (specId: string) => ['reviews', specId] as const,
  /** What needs the signed-in person in a workspace. */
  work: (workspaceId: string) => ['work', workspaceId] as const,
  repositories: (workspaceId: string) => ['repositories', workspaceId] as const,
  reports: (workspaceId: string) => ['reports', workspaceId] as const,
  /** Every proof in a workspace; a spec's own and the specs list's sit under it. */
  proofs: (workspaceId: string) => ['proofs', workspaceId] as const,
  specProofs: (workspaceId: string) => ['proofs', workspaceId, 'specs'] as const,
  proofsOfSpec: (workspaceId: string, specId: string) => ['proofs', workspaceId, specId] as const,
  claims: (workspaceId: string, specNumber: number) =>
    ['proofs', workspaceId, 'claims', specNumber] as const,
};

export function useRequests(workspace: Workspace) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.requests(workspace.id),
    queryFn: () => requestsOf(client, workspace.id),
  });
}

/** The request with a number in the workspace, or null when there's none. */
export function useRequestAt(workspace: Workspace, number: number) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.request(workspace.id, number),
    queryFn: () => requestAt(client, workspace.id, number),
  });
}

export function useTasks(workspace: Workspace) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.tasks(workspace.id),
    queryFn: () => tasksOf(client, workspace.id),
  });
}

export function useSpecTasks(workspace: Workspace, specId: string) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.specTasks(workspace.id, specId),
    queryFn: () => specTasks(client, specId),
  });
}

/** The task with a number in the workspace, or null when there's none. */
export function useTaskAt(workspace: Workspace, number: number) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.task(workspace.id, number),
    queryFn: () => taskAt(client, workspace.id, number),
  });
}

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

export function useReviews(specId: string) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.reviews(specId),
    queryFn: () => reviewsOf(client, specId),
  });
}

export function useWork(workspace: Workspace) {
  const { client, personId } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.work(workspace.id),
    queryFn: () => workOf(client, workspace.id, personId),
  });
}

export function useRepositories(workspace: Workspace) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.repositories(workspace.id),
    queryFn: () => repositoriesOf(client, workspace.id),
  });
}

export function useReports(workspace: Workspace) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.reports(workspace.id),
    queryFn: () => reportsOf(client, workspace.id),
  });
}

export function useProofs(workspace: Workspace) {
  const { client } = useAccount();
  return useSuspenseQuery({
    queryKey: keys.proofs(workspace.id),
    queryFn: () => proofsOf(client, workspace.id),
  });
}

export function useSpecProofs(workspace: Workspace) {
  const { client } = useAccount();
  return useQuery({
    queryKey: keys.specProofs(workspace.id),
    queryFn: () => specProofsOf(client, workspace.id),
  });
}

/** A spec's criteria's proofs, and the tests that name them. */
export function useSpecEvidence(workspace: Workspace, specId: string, specNumber: number) {
  const { client } = useAccount();
  const proofs = useQuery({
    queryKey: keys.proofsOfSpec(workspace.id, specId),
    queryFn: () => proofsOfSpec(client, workspace.id, specId),
  });
  const claims = useQuery({
    queryKey: keys.claims(workspace.id, specNumber),
    queryFn: () => claimsOfSpec(client, workspace.id, specNumber),
  });
  return { proofs, claims };
}

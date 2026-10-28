import { acceptInvitation, offerOf, roleNames } from '@sulba/data/workspaces';
import { Button, buttonClass } from '@sulba/ui/button';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from '@tanstack/react-router';
import { connection, useAccountState } from './account';
import { Centered } from './Centered';
import { Notice } from './Notice';
import { keys } from './queries';
import { signInPath } from './session';

/**
 * Where an invitation link leads: what it offers, and a way to accept it, signing in first when
 * no one is. An expired or revoked link says so and what to do.
 */
export function Join() {
  const { token } = useParams({ from: '/join/$token' });
  const state = useAccountState();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const offer = useQuery({
    queryKey: ['offer', token],
    queryFn: async () => offerOf(await connection(), token),
  });
  const join = useMutation({
    mutationFn: async () => acceptInvitation(await connection(), token),
    onSuccess: async (slug) => {
      await queryClient.invalidateQueries({ queryKey: keys.workspaces });
      await navigate({ to: '/$slug', params: { slug } });
    },
  });

  if (offer.isPending || state.state === 'loading') return null;
  if (offer.isError) {
    return (
      <Centered title="This invitation couldn’t be opened" lead={offer.error.message}>
        <Button variant="outline" onPress={() => void offer.refetch()}>
          Try again
        </Button>
      </Centered>
    );
  }
  if (!offer.data) {
    return (
      <Centered
        title="This invitation has expired"
        lead="An invitation link lasts 7 days, and an admin can revoke it sooner. Ask whoever sent it for a new one."
      >
        <Link to="/">Go to Sulba</Link>
      </Centered>
    );
  }

  const { workspaceName, role } = offer.data;
  const as = roleNames[role].toLowerCase();
  if (state.state === 'out') {
    return (
      <Centered
        title={`Join ${workspaceName}`}
        lead={`You’re invited to join ${workspaceName} as a ${as}. Sign in with GitHub or Google to accept.`}
      >
        <a
          className={buttonClass('primary', 'regular')}
          href={signInPath(window.location.pathname)}
        >
          Sign in
        </a>
      </Centered>
    );
  }

  const who = state.account.email ? `, signed in as ${state.account.email}` : '';
  return (
    <Centered title={`Join ${workspaceName}`} lead={`You’ll join as a ${as}${who}.`}>
      <Notice text={join.error?.message ?? null} />
      <Button onPress={() => join.mutate()} isDisabled={join.isPending}>
        {join.isPending ? 'Joining…' : `Join ${workspaceName}`}
      </Button>
    </Centered>
  );
}
